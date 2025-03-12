#!/usr/bin/env python3

import logging
from pathlib import Path
from pprint import pprint
import re
import ssl
import subprocess
import sys
import traceback
import urllib.request

"""
This is a so called NMS Prime Remote Poller.
It controls the telegraf config – data collected on this machine is sent to a Kafka server.
"""


################################################################################
################################################################################
class NmsPrimeRemotePollerController:

    log_level = logging.INFO

    log_file = "/var/log/nmsprime/remotepoller.log"
    config_file = "/etc/nmsprime/remotepoller.conf"

    config_cache_dir = Path("/var/cache/nmsprime/remotepoller/")
    telegraf_config_dir = Path("/etc/telegraf/telegraf.d")

    nms_config_url = None
    nms_checksum_url = None
    nms_check_certificate = True

    log = None
    config = None
    ssl_context = None
    checksum_new = None
    checksum_old = None

    ################################################################################
    def ex_to_str(self, ex):
        """Converts an exception to a human readable string containing relevant informations.
        Use e.g. to create meaningful log entries."""

        # get type and message of risen exception
        ex_type = f"{type(ex).__name__}"
        ex_args = [f"{a}" for a in ex.args]
        ex_args = ", ".join(ex_args)

        # get the command where the exception has been raised
        tb = traceback.extract_tb(sys.exc_info()[2], limit=2)
        ex_cmd = tb[0][3]
        ex_file = tb[0][0]
        ex_line = tb[0][1]

        nice_ex = f"{ex_type} ({ex_args})"

        return nice_ex

    ############################################################################
    def __init__(self):
        # initalize logger here to be able to log errors in reading config
        # log level may be changed once the configured log level is known
        self._init_logger()

    ############################################################################
    def _init_logger(self):
        self.log = logging.getLogger("NMS Prime Remote Poller")
        logging.basicConfig(
            filename=self.log_file,
            level=self.log_level,
            format="%(asctime)s  %(message)s",
            datefmt="%Y-%m-%d %H:%M-%S",
        )

    ############################################################################
    def read_config(self):
        try:
            with open(self.config_file, "r") as fh:
                lines = fh.readlines()

            for line in lines:
                line = line.strip()

                if not line:
                    continue

                if line[0] in ("#", ";"):
                    continue

                parts = line.split("=")
                if len(parts) != 2:
                    continue

                key = parts[0].strip()
                value = parts[1].strip().replace('"', "").replace("'", "")

                if key == "TELEGRAF_CONFIG_URL":
                    if not value.endswith("/"):
                        value += "/"
                    self.nms_config_url = value + "telegraf.d.tar.gz"
                    self.nms_checksum_url = value + "telegraf.d.tar.gz.sha512sum"
                if key == "CHECK_CERTIFICATE":
                    if value.lower() == "false":
                        self.nms_check_certificate = False
                if key == "LOG_LEVEL":
                    level = re.sub(r"[^a-zA-Z]", "_", value).upper()
                    self.log.setLevel(level)

            if self.nms_config_url is None:
                raise ValueError("Key TELEGRAF_CONFIG_URL missing in config file")

        except Exception as ex:
            self.log.error(f"Error reading {self.config_file}: {self.ex_to_str(ex)}")
            sys.exit(1)

        self.log.debug("Configuration done")

    ############################################################################
    def run(self):

        self._create_ssl_context()
        self._read_remote_checksum()
        self._get_old_checksum()

        if self.checksum_new == self.checksum_old:
            self.log.debug("Config did not change – nothing to do")
            sys.exit(0)

        self.log.info(
            "Remote config has changed – starting process to renew local config"
        )

        self._get_new_config()
        self._extract_new_config()
        self._delete_old_config()
        self._move_new_config()
        self._restart_telegraf()
        self._move_compressed_config()

        self.log.info("Telegraf now running with new configuration.")

    ############################################################################
    def _get_checksum(self, filepath):
        output = subprocess.check_output(f"/usr/bin/sha512sum {filepath}", shell=True)
        return output.decode("utf-8").strip().split(" ")[0]

    ############################################################################
    def _create_ssl_context(self):
        """
        If the server's certificate shall not be checked we need a context to be
        passed to urllib.request.open().
        """
        if not self.nms_check_certificate:
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE

    ############################################################################
    def _read_remote_checksum(self):
        self.log.debug("Getting checksum file.")
        try:
            response = urllib.request.urlopen(
                self.nms_checksum_url, context=self.ssl_context
            )
            self.checksum_new = response.read().decode("utf-8").strip()
        except Exception as ex:
            self.log.warning(f"Error getting checksum file: {self.ex_to_str(ex)}")
            sys.exit(1)

    ############################################################################
    def _get_old_checksum(self):
        self.log.debug("Getting checksum of old config.")

        old_file = self.config_cache_dir / "telegraf.d.tar.gz"
        if not old_file.is_file():
            self.checksum_old = ""
            return

        try:
            self.checksum_old = self._get_checksum(old_file)
        except Exception as ex:
            self.log.warning(
                f"Could not determine checksum for old config: {self.ex_to_str(ex)}"
            )
            self.checksum_old = ""
            return

    ############################################################################
    def _get_new_config(self):
        self.log.debug("Getting new config file.")

        new_file = self.config_cache_dir / "new.telegraf.d.tar.gz"
        try:
            response = urllib.request.urlopen(
                self.nms_config_url, context=self.ssl_context
            )
            data = response.read()
            with open(new_file, "wb") as fh:
                fh.write(data)
            checksum_downloaded = self._get_checksum(new_file)
            if checksum_downloaded != self.checksum_new:
                raise Exception(
                    "Checksum of downloaded file differs from remote checksum."
                )
        except Exception as ex:
            self.log.warning(f"Error getting new config file: {self.ex_to_str(ex)}")
            sys.exit(1)

    ############################################################################
    def _extract_new_config(self):
        self.log.debug("Extracting new config.")

        extract_file = self.config_cache_dir / "new.telegraf.d.tar.gz"
        extract_dir = self.config_cache_dir / "telegraf.d"
        try:
            subprocess.run(f"/usr/bin/rm -rf {extract_dir}", shell=True, check=True)
            subprocess.run(
                f"/usr/bin/tar xf {extract_file} -C {self.config_cache_dir}",
                shell=True,
                check=True,
            )
        except Exception as ex:
            pprint(ex)
            self.log.warning(f"Error getting new config file: {self.ex_to_str(ex)}")
            sys.exit(1)

    ############################################################################
    def _delete_old_config(self):
        self.log.debug(f"Deleting old config in {self.telegraf_config_dir}")
        try:
            subprocess.run(
                f"/usr/bin/rm -rf {self.telegraf_config_dir}/nmsprime__*",
                shell=True,
                check=True,
            )
        except Exception as ex:
            self.log.warning(f"Error deleting old config file: {self.ex_to_str(ex)}")
            sys.exit(1)

    ############################################################################
    def _move_new_config(self):
        self.log.debug(f"Moving new config to {self.telegraf_config_dir}")
        extract_dir = self.config_cache_dir / "telegraf.d"
        try:
            subprocess.run(
                f"/usr/bin/mv -f {extract_dir}/nmsprime__* {self.telegraf_config_dir}",
                shell=True,
                check=True,
            )
            subprocess.run(
                f"/usr/bin/chown root:telegraf {self.telegraf_config_dir}/nmsprime__*",
                shell=True,
                check=True,
            )
            subprocess.run(
                f"/usr/bin/chmod 640 {self.telegraf_config_dir}/nmsprime__*",
                shell=True,
                check=True,
            )
        except Exception as ex:
            self.log.warning(f"Error moving telegraf config: {self.ex_to_str(ex)}")
            sys.exit(1)

    ############################################################################
    def _restart_telegraf(self):
        self.log.debug(f"Restarting telegraf")
        try:
            subprocess.run(
                f"/usr/bin/systemctl restart telegraf.service", shell=True, check=True
            )
        except Exception as ex:
            self.log.warning(f"Error restarting telegraf: {self.ex_to_str(ex)}")
            sys.exit(1)

    ############################################################################
    def _move_compressed_config(self):
        self.log.debug(f"Replacing compressed telegraf config")
        src = self.config_cache_dir / "new.telegraf.d.tar.gz"
        dst = self.config_cache_dir / "telegraf.d.tar.gz"
        try:
            subprocess.run(f"/usr/bin/mv -f {src} {dst}", shell=True, check=True)
        except Exception as ex:
            self.log.warning(
                f"Error moving compressed telegraf config: {self.ex_to_str(ex)}"
            )
            sys.exit(1)


################################################################################
################################################################################
################################################################################
if __name__ == "__main__":
    rp = NmsPrimeRemotePollerController()
    rp.read_config()
    rp.run()
