#!/usr/bin/env python3

import base_data_getter


################################################################################
################################################################################
class Pop3DataGetter(base_data_getter.BaseDataGetter):

    implemented_modes = {
        "simple": "_execute_simple",
    }

    implemented_protos = (
        "POP3",
        "POP3S",
    )

    status_mapping = {
        "Success": 0,
        "Unknown error": 1,
        "OSError": 2,
        "socket.gaierror": 3,
        "TimeoutError": 4,
        "poplib.error_proto": 5,
    }

    ############################################################################
    def _execute_simple(self):

        if self.params["proto"] == "POP3":
            from poplib import POP3 as TEST_POP3_CLASS
        elif self.params["proto"] == "POP3S":
            from poplib import POP3_SSL as TEST_POP3_CLASS

        params = {
            "host": self.params["host"],
            "port": self.params["port"],
            "timeout": self.params["timeout"],
        }

        TEST_POP3_CLASS(**params).getwelcome()

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
    getter = Pop3DataGetter()
    getter.execute()
