#!/usr/bin/env python3

import base64
import base_data_getter
import json
import logging
import os
import re
import sys
import time
import urllib3
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

try:
    import paramiko
except ImportError:
    paramiko = None

try:
    from netmiko import ConnectHandler
    from netmiko.channel import SSHChannel
    from netmiko.exceptions import (
        NetmikoAuthenticationException,
        NetmikoTimeoutException,
        NetmikoBaseException,
    )
    from netmiko.ssh_dispatcher import CLASS_MAPPER
except ImportError:
    ConnectHandler = None
    SSHChannel = None
    CLASS_MAPPER = None
    NetmikoAuthenticationException = None
    NetmikoTimeoutException = None
    NetmikoBaseException = None


LOG_PATH = os.environ.get(
    "DEVICE_CONFIG_BACKUP_LOG",
    "/var/log/nmsprime/device-config-backup.log",
)

LOG_LEVEL_NAMES = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARN": logging.WARNING,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}


class _UtcIsoFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        return datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()


class _BackupContextFilter(logging.Filter):
    def __init__(self, getter):
        super().__init__()
        self.getter = getter

    def filter(self, record):
        record.stage = self.getter.last_debug_stage
        record.sensor_id = self.getter.params.get("sensor_id", "?")
        record.netelement_id = self.getter.params.get("netelement_id", "?")
        record.host = self.getter.params.get("host", "?")
        return True

WEBHOOK_STATUS_SKIPPED = 0
WEBHOOK_STATUS_CONNECTION_FAILED = -1
WEBHOOK_STATUS_TIMEOUT = -2
WEBHOOK_STATUS_SSL_ERROR = -3
WEBHOOK_STATUS_UNKNOWN = -99

LEGACY_FALLBACK_OPENSSH_OPTIONS = {
    "HostKeyAlgorithms": "+ssh-rsa",
    "PubkeyAcceptedAlgorithms": "+ssh-rsa",
    "KexAlgorithms": "diffie-hellman-group14-sha1",
    "Ciphers": "+aes128-cbc",
}

RESERVED_DEVICE_KEYS = {
    "device_type",
    "host",
    "username",
    "password",
    "port",
    "timeout",
    "protocol",
}

ALLOWED_OPENSSH_OPTION_KEYS = frozenset({
    "HostKeyAlgorithms",
    "PubkeyAcceptedAlgorithms",
    "Ciphers",
    "KexAlgorithms",
    "MACs",
    "StrictHostKeyChecking",
    "UserKnownHostsFile",
    "IdentitiesOnly",
    "PasswordAuthentication",
    "PreferredAuthentications",
})

NETMIKO_KWARG_KEYS = frozenset({
    "global_delay_factor",
    "fast_cli",
    "conn_timeout",
    "auth_timeout",
    "banner_timeout",
    "keepalive",
    "default_enter",
    "session_timeout",
    "blocking_timeout",
    "read_timeout_override",
})


################################################################################
class BackupException(Exception):
    def __init__(self, message, status_code, stage):
        super().__init__(message)
        self.status_code = status_code
        self.stage = stage


class ConnectionFailedException(BackupException):
    def __init__(self, message="Connection failed"):
        super().__init__(message, 2, 1)


class AuthenticationFailedException(BackupException):
    def __init__(self, message="Authentication failed"):
        super().__init__(message, 3, 2)


class ConfigCommandFailedException(BackupException):
    def __init__(self, message="Config command failed"):
        super().__init__(message, 5, 3)


class WebhookFailedException(BackupException):
    def __init__(self, message="Webhook POST failed"):
        super().__init__(message, 6, 4)


class EmptyConfigException(BackupException):
    def __init__(self, message="Empty config received"):
        super().__init__(message, 7, 3)


class InvalidConfigurationException(BackupException):
    def __init__(self, message="Invalid configuration"):
        super().__init__(message, 8, 0)


################################################################################
def _make_pre_handshake_connection_class(base_class, security_helper, openssh_options):
    """Subclass the Netmiko device driver (not ConnectHandler, which is a factory)."""
    parent_establish = base_class.establish_connection

    def establish_connection(self, width=511, height=1000):
        if self.protocol != "ssh" or not openssh_options:
            return parent_establish(self, width, height)

        import socket

        ssh_connect_params = self._connect_params_dict()
        self.remote_conn_pre = self._build_ssh_client()

        try:
            security_helper._connect_ssh_client_pre_handshake(
                self.remote_conn_pre,
                ssh_connect_params,
                openssh_options,
            )
        except socket.error as conn_error:
            self.paramiko_cleanup()
            msg = f"""TCP connection to device failed.

Common causes of this problem are:
1. Incorrect hostname or IP address.
2. Wrong TCP port.
3. Intermediate firewall blocking access.

Device settings: {self.device_type} {self.host}:{self.port}

"""
            if "Name or service not known" in str(conn_error):
                msg = (
                    f"DNS failure--the hostname you provided was not resolvable "
                    f"in DNS: {self.host}:{self.port}"
                )
            raise NetmikoTimeoutException(msg.lstrip()) from conn_error
        except paramiko.ssh_exception.AuthenticationException as auth_err:
            self.paramiko_cleanup()
            msg = f"""Authentication to device failed.

Common causes of this problem are:
1. Invalid username and password
2. Incorrect SSH-key file
3. Connecting to the wrong device

Device settings: {self.device_type} {self.host}:{self.port}

"""
            msg += self.RETURN + str(auth_err)
            raise NetmikoAuthenticationException(msg) from auth_err
        except paramiko.ssh_exception.SSHException as ex:
            self.paramiko_cleanup()
            if "No existing session" in str(ex):
                msg = (
                    "Paramiko: 'No existing session' error: "
                    "try increasing 'conn_timeout' to 15 seconds or larger."
                )
                raise NetmikoTimeoutException(msg) from ex
            msg = f"""
A paramiko SSHException occurred during connection creation:

{str(ex)}

"""
            raise NetmikoTimeoutException(msg) from ex

        if self.verbose:
            print(f"SSH connection established to {self.host}:{self.port}")

        self.remote_conn = self.remote_conn_pre.invoke_shell(
            term="vt100", width=width, height=height
        )
        self.remote_conn.settimeout(self.blocking_timeout)
        if self.keepalive:
            self.remote_conn.transport.set_keepalive(self.keepalive)

        self.channel = SSHChannel(conn=self.remote_conn, encoding=self.encoding)
        self.special_login_handler()
        if self.verbose:
            print("Interactive SSH session established")

        return None

    return type(
        f"PreHandshake{base_class.__name__}",
        (base_class,),
        {"establish_connection": establish_connection},
    )


################################################################################
class NetElementConfigBackupDataGetter(base_data_getter.BaseDataGetter):

    implemented_modes = {
        "default": "_execute_default",
    }

    status_mapping = {
        "Success": 0,
        "Unknown error": 1,
        "ConnectionFailedException": 2,
        "AuthenticationFailedException": 3,
        "ConfigCommandFailedException": 5,
        "WebhookFailedException": 6,
        "EmptyConfigException": 7,
        "InvalidConfigurationException": 8,
    }

    def __init__(self):
        self.error_stage = 0
        self.config_size = 0
        self.webhook_status = 0
        self.webhook_error_detail = ""
        self.error_message = ""
        self.last_debug_stage = "init"
        super().__init__()
        self._setup_logging()
        self._log("init", f"Loaded config file {sys.argv[1]}")

    ############################################################################
    def _setup_logging(self):
        self._logger = logging.getLogger(__name__)
        self._logger.handlers.clear()
        self._logger.setLevel(logging.DEBUG)
        self._logger.propagate = False

        handler_level = logging.DEBUG if self.debug else logging.WARNING
        formatter = _UtcIsoFormatter(
            "%(asctime)s [%(levelname)s] stage=%(stage)s "
            "sensor=%(sensor_id)s netelement=%(netelement_id)s host=%(host)s %(message)s"
        )
        context_filter = _BackupContextFilter(self)

        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(handler_level)
        stderr_handler.setFormatter(formatter)
        stderr_handler.addFilter(context_filter)
        self._logger.addHandler(stderr_handler)

        try:
            Path(LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
            file_handler.setLevel(handler_level)
            file_handler.setFormatter(formatter)
            file_handler.addFilter(context_filter)
            self._logger.addHandler(file_handler)
        except OSError as log_error:
            if self.debug:
                print(
                    f"Could not write debug log to {LOG_PATH}: {log_error}",
                    file=sys.stderr,
                )

    ############################################################################
    def _log(self, stage, message, level="DEBUG", exc=None):
        self.last_debug_stage = stage
        log_level = LOG_LEVEL_NAMES.get(level, logging.DEBUG)

        if exc is not None:
            message = f"{message} ({type(exc).__name__}: {exc})"

        self._logger.log(
            log_level,
            message,
            exc_info=exc is not None and self.debug,
        )

    ############################################################################
    def _coerce_option_value(self, value):
        if value.lower() in {"true", "false"}:
            return value.lower() == "true"
        if value.isdigit():
            return int(value)
        try:
            return float(value)
        except ValueError:
            return value

    ############################################################################
    def _parse_connection_options(self):
        raw = self.params.get("connection_options_b64")
        if not raw:
            return {}, {}

        try:
            text = base64.b64decode(raw).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as ex:
            raise InvalidConfigurationException(f"Invalid connection_options_b64: {ex}") from ex

        openssh_options = {}
        netmiko_kwargs = {}

        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if not key or key in RESERVED_DEVICE_KEYS:
                    continue

                if key in NETMIKO_KWARG_KEYS:
                    netmiko_kwargs[key] = self._coerce_option_value(value)
                    continue

                if key in ALLOWED_OPENSSH_OPTION_KEYS:
                    openssh_options[key] = value
                    continue

                self._log(
                    "connection",
                    f"Ignoring unsupported connection option {key!r}",
                    level="WARN",
                )
                continue

            parts = line.split(None, 1)
            key = parts[0]
            value = parts[1] if len(parts) > 1 else ""
            if not key or key in RESERVED_DEVICE_KEYS:
                continue

            if key not in ALLOWED_OPENSSH_OPTION_KEYS:
                self._log(
                    "connection",
                    f"Ignoring unsupported connection option {key!r}",
                    level="WARN",
                )
                continue

            openssh_options[key] = value

        return openssh_options, netmiko_kwargs

    ############################################################################
    def _parse_openssh_algorithm_value(self, value):
        append_mode = False
        algorithms = []

        for token in (value or "").replace(",", " ").split():
            token = token.strip()
            if not token:
                continue
            if token.startswith("+"):
                append_mode = True
                token = token[1:]
            elif token.startswith("-"):
                continue
            if token:
                algorithms.append(token)

        return append_mode, algorithms

    ############################################################################
    def _merge_algorithm_list(self, current, new, append_mode):
        if append_mode:
            merged = list(current)
            for algorithm in new:
                if algorithm not in merged:
                    merged.append(algorithm)
            return merged

        return list(new) if new else list(current)

    ############################################################################
    def _apply_algorithm_list(self, opts, field, info_attr, algorithms):
        if not algorithms:
            return

        transport = opts._transport
        known = set(getattr(transport, info_attr).keys())
        filtered = [algorithm for algorithm in algorithms if algorithm in known]
        unknown = [algorithm for algorithm in algorithms if algorithm not in known]
        if unknown:
            self._log(
                "connection",
                f"Ignoring unsupported {field} algorithms: {unknown}",
                level="WARN",
            )

        if not filtered:
            return

        try:
            setattr(opts, field, tuple(filtered))
        except (TypeError, ValueError) as ex:
            self._log(
                "connection",
                f"Could not apply {field} algorithms {filtered}: {ex}",
                level="WARN",
            )

    ############################################################################
    def _set_security_algorithms(self, opts, field, info_attr, value):
        append_mode, algorithms = self._parse_openssh_algorithm_value(value)
        if not algorithms and not append_mode:
            return

        current = list(getattr(opts, field))
        merged = self._merge_algorithm_list(current, algorithms, append_mode)
        self._apply_algorithm_list(opts, field, info_attr, merged)

    ############################################################################
    def _configure_transport_pre_handshake(self, transport, openssh_options):
        """Apply OpenSSH algorithm preferences before Transport.start_client()."""
        if not openssh_options:
            return

        opts = transport.get_security_options()
        key_types = list(opts.key_types)

        if "HostKeyAlgorithms" in openssh_options:
            append_mode, algorithms = self._parse_openssh_algorithm_value(
                openssh_options["HostKeyAlgorithms"]
            )
            key_types = self._merge_algorithm_list(key_types, algorithms, append_mode)

        if "PubkeyAcceptedAlgorithms" in openssh_options:
            append_mode, algorithms = self._parse_openssh_algorithm_value(
                openssh_options["PubkeyAcceptedAlgorithms"]
            )
            key_types = self._merge_algorithm_list(key_types, algorithms, append_mode)

        if "HostKeyAlgorithms" in openssh_options or "PubkeyAcceptedAlgorithms" in openssh_options:
            self._apply_algorithm_list(opts, "key_types", "_key_info", key_types)

        if "KexAlgorithms" in openssh_options:
            self._set_security_algorithms(
                opts,
                "kex",
                "_kex_info",
                openssh_options["KexAlgorithms"],
            )

        if "Ciphers" in openssh_options:
            self._set_security_algorithms(
                opts,
                "ciphers",
                "_cipher_info",
                openssh_options["Ciphers"],
            )

        if "MACs" in openssh_options:
            self._set_security_algorithms(
                opts,
                "digests",
                "_mac_info",
                openssh_options["MACs"],
            )

        applied = [
            key
            for key in ("HostKeyAlgorithms", "PubkeyAcceptedAlgorithms", "KexAlgorithms", "Ciphers", "MACs")
            if key in openssh_options
        ]
        self._log("connection", f"Configured pre-handshake Paramiko security options for {applied}")

    ############################################################################
    def _connect_ssh_client_pre_handshake(self, client, connect_params, openssh_options):
        """Connect via Paramiko with security options applied before handshake."""

        def transport_factory(sock, disabled_algorithms=None, **kwargs):
            transport = paramiko.Transport(sock, disabled_algorithms=disabled_algorithms)
            self._configure_transport_pre_handshake(transport, openssh_options)
            return transport

        params = dict(connect_params)
        params["transport_factory"] = transport_factory
        client.connect(**params)

    ############################################################################
    def _paramiko_supports_host_key(self, algorithm):
        if paramiko is None:
            return False

        return algorithm in paramiko.transport.Transport._key_info

    ############################################################################
    def _validate_openssh_options(self, openssh_options):
        if not openssh_options:
            return

        combined = " ".join(
            openssh_options.get(key, "")
            for key in ("HostKeyAlgorithms", "PubkeyAcceptedAlgorithms")
        )
        if "ssh-dss" not in combined:
            return

        if self._paramiko_supports_host_key("ssh-dss"):
            return

        raise InvalidConfigurationException(
            "HostKeyAlgorithms include ssh-dss but Paramiko "
            f"{getattr(paramiko, '__version__', '?')} does not support DSA host keys; "
            "install paramiko<4 (for example 3.5.1)"
        )

    ############################################################################
    def _sanitize_config_output(self, text):
        if not text:
            return text

        raw_size = len(text.encode("utf-8"))
        ansi_patterns = [
            r"\x1b\[[0-9;]*m",
            r"\x1b\[[0?]*;?[0-9;]*[ -/]*[@-~]",
            r"\x1b[@-Z\\-_]",
            r"\x1b\][^\x07]*(?:\x07|\x1b\\)",
        ]

        for pattern in ansi_patterns:
            text = re.sub(pattern, "", text)

        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\\\n\s*", "", text)

        clean_size = len(text.encode("utf-8"))
        if clean_size != raw_size:
            self._log(
                "config_command",
                f"Sanitized config output ({raw_size} -> {clean_size} bytes)",
            )

        return text.strip()

    ############################################################################
    def _is_handshake_failure(self, exc):
        message = str(exc).lower()
        return any(
            token in message
            for token in (
                "no acceptable host key",
                "incompatible ssh peer",
                "incompatible peer",
                "sshexception occurred during connection",
                "negotiation failed",
            )
        )

    ############################################################################
    def _open_netmiko_connection(self, device, openssh_options):
        if not openssh_options:
            return ConnectHandler(**device)

        device_type = device.get("device_type")
        base_class = CLASS_MAPPER.get(device_type) if CLASS_MAPPER else None
        if base_class is None:
            return ConnectHandler(**device)

        connection_class = _make_pre_handshake_connection_class(
            base_class,
            self,
            openssh_options,
        )
        return connection_class(**device)

    ############################################################################
    def _resolve_device_type(self):
        device_type = (self.params.get("device_type") or "").strip()
        if not device_type:
            raise InvalidConfigurationException("device_type is required")

        protocol = (self.params.get("protocol") or "ssh").strip().lower()
        if protocol == "telnet" and not device_type.endswith("_telnet"):
            return f"{device_type}_telnet"

        return device_type

    ############################################################################
    def _build_device_params(self):
        config_command = (self.params.get("config_command") or "").strip()
        if not config_command:
            raise InvalidConfigurationException("config_command is required")

        openssh_options, netmiko_kwargs = self._parse_connection_options()
        device = {
            "device_type": self._resolve_device_type(),
            "host": self.params["host"],
            "username": self.params["username"],
            "password": self.params["password"],
            "port": int(self.params["port"]),
            "timeout": int(self.params["timeout"]),
            **netmiko_kwargs,
        }

        self._log(
            "connection",
            (
                f"Prepared netmiko session device_type={device['device_type']} "
                f"host={device['host']}:{device['port']} command={config_command!r} "
                f"openssh_options={list(openssh_options.keys())} netmiko_kwargs={list(netmiko_kwargs.keys())}"
            ),
        )

        return device, config_command, openssh_options

    ############################################################################
    def execute(self):
        start_time = time.time()
        self.status = 0

        try:
            if ConnectHandler is None:
                raise BackupException("netmiko is not installed", 1, 0)
            if paramiko is None:
                raise BackupException("paramiko is not installed", 1, 0)
            if requests is None:
                raise BackupException("requests is not installed", 1, 0)

            self._execute_default(start_time)
            self.error_message = ""
            self._log("complete", f"Backup finished successfully in {time.time() - start_time:.3f}s")
        except BackupException as ex:
            self.status = ex.status_code
            self.error_stage = ex.stage
            self.error_message = str(ex)
            self._log("failed", self.error_message, level="ERROR", exc=ex)
        except Exception as ex:
            self.status = 1
            self.error_message = f"{type(ex).__name__}, {ex.args}"
            self._log("failed", self.error_message, level="ERROR", exc=ex)

        self.execution_time = time.time() - start_time
        self._generate_output()
        self._print_output()

    ############################################################################
    def _execute_default(self, start_time):
        device, config_command, openssh_options = self._build_device_params()
        device_os = self.params.get("device_type")

        self._log("collect_config", "Starting netmiko session")
        config = self._collect_config(device, config_command, openssh_options)
        if not config or not config.strip():
            raise EmptyConfigException()

        self.config_size = len(config.encode("utf-8"))
        self._log("collect_config", f"Collected config ({self.config_size} bytes)")
        self._post_webhook(device_os, config, start_time)

    ############################################################################
    def _collect_config(self, device, config_command, openssh_options):
        self._validate_openssh_options(openssh_options)

        connection = None
        attempts = []

        if openssh_options:
            attempts.append(("configured", openssh_options))
            attempts.append(("legacy_fallback", LEGACY_FALLBACK_OPENSSH_OPTIONS))
        else:
            attempts.append(("default", {}))

        last_error = None
        read_timeout = max(int(self.params["timeout"]), 180)

        for attempt_name, attempt_options in attempts:
            try:
                self._log("connection", f"Trying netmiko pre-handshake connection ({attempt_name})")
                connection = self._open_netmiko_connection(device, attempt_options)
                output = connection.send_command(
                    config_command,
                    read_timeout=read_timeout,
                )
                output = self._sanitize_config_output(output)
                if not output:
                    raise ConfigCommandFailedException(
                        f"No output received for command: {config_command}"
                    )

                self._log(
                    "config_command",
                    f"Collected {len(output.encode('utf-8'))} bytes of command output via {attempt_name}",
                )
                return output
            except NetmikoAuthenticationException as ex:
                raise AuthenticationFailedException(str(ex)) from ex
            except ConfigCommandFailedException:
                raise
            except (NetmikoTimeoutException, NetmikoBaseException, Exception) as ex:
                last_error = ex
                if not self._is_handshake_failure(ex):
                    if isinstance(ex, NetmikoTimeoutException):
                        raise ConnectionFailedException(str(ex)) from ex
                    if isinstance(ex, NetmikoBaseException):
                        raise ConfigCommandFailedException(str(ex)) from ex
                    raise ConnectionFailedException(str(ex)) from ex

                self._log(
                    "connection",
                    f"netmiko handshake attempt {attempt_name} failed: {ex}",
                    level="WARN",
                )
            finally:
                if connection is not None:
                    try:
                        connection.disconnect()
                    except Exception:
                        pass
                    connection = None

        raise ConnectionFailedException(str(last_error) if last_error else "SSH connection failed")

    ############################################################################
    def _truncate_text(self, text, limit=500):
        text = (text or "").strip()
        if len(text) <= limit:
            return text

        return text[:limit] + "…"

    ############################################################################
    def _webhook_failure(self, message, status_code=WEBHOOK_STATUS_UNKNOWN, response_body=""):
        self.webhook_status = status_code
        detail = response_body or message
        self.webhook_error_detail = self._truncate_text(detail, limit=500)
        self._log(
            "webhook",
            f"Webhook failed status={status_code} message={message} detail={self.webhook_error_detail}",
            level="ERROR",
        )
        raise WebhookFailedException(message)

    ############################################################################
    def _post_webhook(self, device_os, config, start_time):
        webhook_url = self.params.get("webhook_url")
        if not webhook_url:
            self.webhook_status = WEBHOOK_STATUS_SKIPPED
            self.webhook_error_detail = "webhook_url not configured"
            self._log("webhook", "Skipped because webhook_url is empty", level="WARN")
            return

        payload = {
            "netelement_id": self.params["netelement_id"],
            "sensor_id": self.params["sensor_id"],
            "device_os": device_os,
            "protocol": self.params.get("protocol"),
            "host": self.params["host"],
            "runtime": round(time.time() - start_time, 3),
            "config_size_bytes": self.config_size,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "config": config,
        }
        payload_size = len(json.dumps(payload).encode("utf-8"))

        self._log(
            "webhook",
            f"POST {webhook_url} payload_bytes={payload_size} timeout={self.params['timeout']}s",
        )

        verify_ssl = not str(webhook_url).lower().startswith("https://")
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            self._log("webhook", "SSL certificate verification disabled for internal webhook")

        try:
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=int(self.params["timeout"]),
                verify=verify_ssl,
            )
            self.webhook_status = response.status_code
            if response.status_code >= 400:
                response_body = response.text or ""
                message = (
                    f"Webhook HTTP {response.status_code} "
                    f"POST {webhook_url}"
                )
                if response_body:
                    message = f"{message}: {self._truncate_text(response_body)}"
                self._webhook_failure(message, status_code=response.status_code, response_body=response_body)

            self.webhook_error_detail = ""
            self._log("webhook", f"Accepted with HTTP {self.webhook_status}")
        except requests.exceptions.Timeout as ex:
            message = f"Webhook timeout POST {webhook_url} after {self.params['timeout']}s"
            self._webhook_failure(
                message,
                status_code=WEBHOOK_STATUS_TIMEOUT,
                response_body=str(ex),
            )
        except requests.exceptions.SSLError as ex:
            message = f"Webhook SSL error POST {webhook_url}: {ex}"
            self._webhook_failure(
                message,
                status_code=WEBHOOK_STATUS_SSL_ERROR,
                response_body=str(ex),
            )
        except requests.exceptions.ConnectionError as ex:
            message = f"Webhook transport error POST {webhook_url}: {ex}"
            self._webhook_failure(
                message,
                status_code=WEBHOOK_STATUS_CONNECTION_FAILED,
                response_body=str(ex),
            )
        except Exception as ex:
            message = f"Webhook failed POST {webhook_url}: {type(ex).__name__}, {ex.args}"
            self._webhook_failure(
                message,
                status_code=WEBHOOK_STATUS_UNKNOWN,
                response_body=str(ex),
            )

    ############################################################################
    def _generate_output(self):
        self.output_data = {
            "name": self.params["metric_name"],
            "netelementid": self.params["netelement_id"],
            "sensorid": self.params["sensor_id"],
            "status_code": self.status,
            "error_stage": self.error_stage,
            "runtime": round(self.execution_time or 0, 3),
            "config_size_bytes": self.config_size,
            "webhook_status_code": self.webhook_status,
            "webhook_error_detail": self.webhook_error_detail,
            "debug_stage": self.last_debug_stage,
            "error_message": self.error_message,
        }


################################################################################
if __name__ == "__main__":
    getter = NetElementConfigBackupDataGetter()
    getter.execute()
