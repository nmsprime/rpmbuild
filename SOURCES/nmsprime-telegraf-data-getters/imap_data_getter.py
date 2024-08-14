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
        "TimeoutError": 4,
        "IMAP4.error": 5,
        "IMAP4.abort": 6,
        "IMAP4.readonly": 7,
    }

    ############################################################################
    def __init__(self):
        super().__init__()

    ############################################################################
    def timeout(max_time):
        """
        Timeout decorator, parameter in seconds.
        Unfortunately the timeout param has been added to IPAM4 call not before version 3.9…
        The thread would run forever but will be killed by the timeout defined on telegraf.
        Remove that workaround once we get a python version >=3.9
        """

        def timeout_decorator(item):
            """Wrap the original function."""

            if sys.version_info[0] > 2 and sys.version_info[1] > 8:
                # nothing to do
                return

            @functools.wraps(item)
            def func_wrapper(*args, **kwargs):
                """Closure for function."""
                pool = multiprocessing.pool.ThreadPool(processes=1)
                async_result = pool.apply_async(item, args, kwargs)
                # raises a TimeoutError if execution exceeds max_timeout
                return async_result.get(max_time)

            return func_wrapper

        return timeout_decorator

    ############################################################################
    # decorator param can't access dynamically created values in global or class variables
    @timeout(10.5 if len(sys.argv) == 2 else int(sys.argv[2]) * 1.05)
    def _execute_simple(self):

        if self.params["proto"] == "IMAP":
            from imaplib import IMAP4 as TEST_IMAP_CLASS
        elif self.params["proto"] == "IMAPS":
            from imaplib import IMAP4_SSL as TEST_IMAP_CLASS

        params = {
            "host": self.params["host"],
            "port": self.params["port"],
        }
        if sys.version_info[0] > 2 and sys.version_info[1] > 8:
            params["timeout"] = self.params["timeout"]

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
