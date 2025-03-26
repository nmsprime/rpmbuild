#!/usr/bin/env python3

import base_data_getter
import functools
import multiprocessing.pool
import sys


################################################################################
################################################################################
class ImapDataGetter(base_data_getter.BaseDataGetter):

    params = dict()

    implemented_modes = {
        "simple": "_execute_simple",
    }

    implemented_protos = (
        "IMAP",
        "IMAPS",
    )

    status_mapping = {
        "Success": 0,
        "Unknown error": 1,
        "OSError": 2,
        "socket.gaierror": 3,
        "gaierror": 3,
        "TimeoutError": 4,
        "IMAP4.error": 5,
        "IMAP4.abort": 6,
        "IMAP4.readonly": 7,
        "PythonVersionException": 8,
    }

    ############################################################################
    def _execute_simple(self):

        # needs at least Python 3.9 to have the timeout argument in IMAP
        if sys.version_info[0] < 3 or sys.version_info[1] < 9:
            raise base_data_getter.PythonVersionException()

        if self.params["proto"] == "IMAP":
            from imaplib import IMAP4 as TEST_IMAP_CLASS
        elif self.params["proto"] == "IMAPS":
            from imaplib import IMAP4_SSL as TEST_IMAP_CLASS

        params = {
            "host": self.params["host"],
            "port": self.params["port"],
            "timeout": self.params["timeout"],
        }

        with TEST_IMAP_CLASS(**params) as imap:
            imap.noop()

    ############################################################################
    def _generate_output(self):
        self.output_data = {
            "name": self.params["metric_name"],
            "netelementid": self.params["netelement_id"],
            "sensorid": self.params["sensor_id"],
            "status_code": self.status,
            "runtime": round(self.execution_time, 3),
            "error_message": self.error_message,
        }


################################################################################
################################################################################
if __name__ == "__main__":
    getter = ImapDataGetter()
    getter.execute()
