#!/usr/bin/env python3

import json
from pprint import pprint
import sys
import time


################################################################################
################################################################################
class BaseDataGetter:

    debug = False

    implemented_modes = dict()
    params = dict()

    status = None
    execution_time = None

    # Overwrite for your derived data getter
    # Your dict must contain at least these two keys
    status_mapping = {
        "Success": 0,
        "Unknown error": 1,
    }

    ############################################################################
    def __init__(self):
        self._read_args()
        self._read_configfile()

    ############################################################################
    def usage(self, retcode=0):
        if retcode:
            print()
            print(32 * "=")
            print("ERROR")
            print(32 * "=")
        print()
        print("USAGE:")
        print(f"/usr/bin/env python3 {sys.argv[0]} CONFIGFILE [--debug]")
        print()
        print(
            "The optional --debug gives more output; otherwise there will only be JSON."
        )
        print()
        print(64 * "-")
        print("And here are the status_code value mappings for your diagram")
        for k, v in self.status_mapping.items():
            print(f"    {v} ⇒ {k}")
        print()
        sys.exit(retcode)

    ############################################################################
    def out(self, data):
        print()
        print("----- DEBUG -----")
        print(f"{type(data)}: ", end="")
        pprint(data)
        print()

    ############################################################################
    def _read_args(self):
        if len(sys.argv) < 2:
            self.usage(1)

        if "--debug" in sys.argv:
            self.debug = True

    ############################################################################
    def _read_configfile(self):
        if self.debug:
            print("Reading configfile…")
        try:
            with open(sys.argv[1], "r") as fh:
                lines = fh.readlines()
        except Exception as ex:
            print(f"Error reading configfile “{sys.argv[1]}”:")
            print(f"{type(ex).__name__}, {ex.args}")
            sys.exit(1)

        for line in lines:
            line = line.strip()
            if line.startswith("# extCommandConfig::"):
                self._process_config_line(line)

        if self.debug:
            print("Done. Config is:")
            pprint(self.params)

    ############################################################################
    def _process_config_line(self, line):

        parts = line.split("::")
        _ = parts.pop(0)

        param_type = parts.pop(0)
        param_name = parts.pop(0)
        param_value = "::".join(parts)

        if param_type == "integer":
            param_value = int(param_value)
        if param_type == "float":
            param_value = float(param_value)

        self.params[param_name] = param_value

    ############################################################################
    def execute(self):
        start_time = time.time()

        try:
            method_name = self.implemented_modes[self.params["mode"]]
            getattr(self, method_name)()
            self.status = 0
            self.error_message = ""
        except Exception as ex:
            self.error_message = f"{type(ex).__name__}, {ex.args}"
            if self.debug:
                print(f"Error in execute(): {self.error_message}")
            ex_type = f"{type(ex).__name__}"
            if ex_type in self.status_mapping.keys():
                key = ex_type
            else:
                key = "Unknown error"
            self.status = self.status_mapping[key]

        self.execution_time = time.time() - start_time

        self._generate_output()
        self._print_output()

    ############################################################################
    def _print_output(self):
        print(json.dumps(self.output_data))
