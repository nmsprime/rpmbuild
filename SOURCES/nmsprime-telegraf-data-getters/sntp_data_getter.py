#!/usr/bin/env python3

import ipaddress
import json
from pprint import pprint
import re
import subprocess
import sys
import time


class SntpDataGetter:

    # debug = True
    debug = False

    binary = "/usr/sbin/sntp"
    timeout = 2

    status_mapping = {
        "success": 0,
        "timeout": 1,
        "dns_error": 2,
        "sntp_not_found": 3,
        "sntp_no_permission": 4,
        "unknown_error": 9,
    }

    server = None

    ############################################################################
    def out(self, data):
        print("----- DEBUG -----")
        print(f"{type(data)}: ", end="")
        pprint(data)
        print()

    ############################################################################
    def usage(self):
        print()
        print("USAGE:")
        print(f"/usr/bin/env python3 {sys.argv[0]} SERVER ID NAME")
        print("     - SERVER: SNTP server to ask (IPv4, IPv6 hostname or FQDN)")
        print("     - ID: NMS Prime netelement_id")
        print("     - NAME: name to identify metric")
        print()
        print("And here are the status_code value mappings for your diagram")
        for k, v in self.status_mapping.items():
            print(f"    {v} ⇒ {k}")
        print()

    ############################################################################
    def __init__(self):
        if self.debug:
            print()
            print("DEBUG MODE ENABLED")
            print()

        if not self._check_input():
            print()
            print("ERROR")
            self.usage()
            sys.exit(1)

        self.server = sys.argv[1]
        self.netelement_id = int(sys.argv[2])
        self.metric_name = sys.argv[3]
        self.sensor_id = int(sys.argv[4])

    ############################################################################
    def execute(self):

        self._build_and_run_command()
        self.output = self._build_output()
        self._print_output()

    ############################################################################
    def _check_input(self):

        if len(sys.argv) == 2:
            if sys.argv[1] in ["-h", "--help", "?"]:
                self.usage()
                sys.exit(0)

        if len(sys.argv) != 5:
            return False

        return self._check_ip_or_host() and self._check_netelement_id()

    ############################################################################
    def _check_ip_or_host(self):
        try:
            ipaddress.ip_address(sys.argv[1])
            return True
        except ValueError:
            # not an IPv4 or IPv6 address – check if hostname or FQDN
            regex = "^([a-zA-Z0-9.-]+)$"
            if re.match(regex, sys.argv[1]):
                return True
        except Exception:
            # something unexpected happened – stop here
            return False

        return False

    ############################################################################
    def _check_netelement_id(self):
        try:
            net_id = int(sys.argv[2])
        except Exception:
            return False

        if net_id < 1:
            return False

        return True

    ############################################################################
    def _build_and_run_command(self):
        cmd = [self.binary, "-t", str(self.timeout), self.server]

        try:
            self.start_time = time.time()
            out_text = subprocess.check_output(cmd, timeout=self.timeout).decode(
                "utf-8"
            )
            self.stop_time = time.time()
            self.sntp_return_code = 0
        except FileNotFoundError as e:
            self.stop_time = time.time()
            out_text = e.strerror
            self.sntp_return_code = 1000
        except PermissionError as e:
            self.stop_time = time.time()
            out_text = e.strerror
            self.sntp_return_code = 1001
        except subprocess.TimeoutExpired as e:
            self.stop_time = time.time()
            out_text = e.output.decode("utf-8")
            self.sntp_return_code = 1002
        except subprocess.CalledProcessError as e:
            # in this case the sntp command itself exited with a non-zero status
            self.stop_time = time.time()
            out_text = e.output.decode("utf-8")
            self.sntp_return_code = e.returncode
        except Exception as e:
            # catch all – some unexpected exception
            self.stop_time = time.time()
            out_text = e.strerror
            self.sntp_return_code = 2000

        self.sntp_return_data = out_text

        if self.debug:
            self.out(self.sntp_return_code)
            self.out(self.sntp_return_data)

    ############################################################################
    def _build_output(self):

        output = {
            "name": f"{self.metric_name}",
            "server": self.server,
            "netelementid": self.netelement_id,
            "sensorid": self.sensor_id,
        }

        output["exec_time"] = round((self.stop_time - self.start_time), 6)

        if self.sntp_return_code == 0:
            output["status_code"] = self.status_mapping["success"]
            output["offset"] = self._calculate_offset()
            output["max_error"] = self._calculate_max_error()
            return output

        # SNTP returned an error
        output["offset"] = None
        output["max_error"] = None

        if self.sntp_return_code == 1000:
            output["status_code"] = self.status_mapping["sntp_not_found"]
            return output

        if self.sntp_return_code == 1001:
            output["status_code"] = self.status_mapping["sntp_no_permission"]
            return output

        if self.sntp_return_code == 1002:
            output["status_code"] = self.status_mapping["timeout"]
            return output

        if self.sntp_return_code == 2000:
            output["status_code"] = self.status_mapping["unknown_error"]
            return output

        output["status_code"] = self._determine_status()
        output["offset"] = None
        output["max_error"] = None

        return output

    ############################################################################
    def _calculate_offset(self):
        output_offset = 0.0
        for line in self.sntp_return_data.split("\n")[1:]:
            if not line:
                continue

            offset = float(line.split(" ")[3])

            if abs(offset) > abs(output_offset):
                output_offset = offset

        return output_offset

    ############################################################################
    def _calculate_max_error(self):
        output_error = None
        for line in self.sntp_return_data.split("\n")[1:]:

            if not line:
                continue

            error = line.split(" ")[5]
            if error == "?":
                continue

            error = float(error)
            if output_error is None:
                output_error = error
                continue

            if error > output_error:
                output_error = error

        return output_error

    ############################################################################
    def _determine_status(self):
        lines = self.sntp_return_data.split("\n")

        if not "Started sntp" in lines[0]:
            # sntp command could not be started
            return self.status_mapping["unknown_error"]

        for line in lines:
            if "Error looking up" in line or "Unable to resolve hostname" in line:
                return self.status_mapping["dns_error"]

        return self.status_mapping["success"]

    ############################################################################
    def _print_output(self):
        print(json.dumps(self.output))


################################################################################
################################################################################
################################################################################
if __name__ == "__main__":

    datagetter = SntpDataGetter()
    datagetter.execute()
