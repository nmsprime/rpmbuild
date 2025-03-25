#!/usr/bin/env python3

import base_data_getter


################################################################################
################################################################################
class SntpDataGetter(base_data_getter.BaseDataGetter):

    implemented_modes = {
        "default": "_execute_default",
    }

    status_mapping = {
        "Success": 0,
        "Unknown error": 1,
        "ModuleNotFoundError": 2,
        "socket.gaierror": 3,
        "ntplib.NTPException": 4,
        "NTPException": 4,
    }

    delay = None
    offset = None
    root_delay = None
    root_dispersion = None
    stratum = None

    ############################################################################
    def _execute_default(self):

        # ntplib is not part of standard Python (installed via EPEL or venv)
        # import here to catch missing module
        import ntplib

        ntp_client = ntplib.NTPClient()
        response = ntp_client.request(
            self.params["host"],
            version=self.params["version"],
            port=self.params["port"],
            timeout=self.params["timeout"],
        )

        self.delay = response.delay
        self.offset = response.offset
        self.root_delay = response.root_delay
        self.root_dispersion = response.root_dispersion
        self.stratum = response.stratum

    ############################################################################
    def _generate_output(self):
        self.output_data = {
            "name": self.params["metric_name"],
            "netelementid": self.params["netelement_id"],
            "sensorid": self.params["sensor_id"],
            "status_code": self.status,
            "runtime": round(self.execution_time, 3),
            "error_message": self.error_message,
            "delay": self.delay,
            "offset": self.offset,
            "root_delay": self.root_delay,
            "root_dispersion": self.root_dispersion,
            "stratum": self.stratum,
        }


################################################################################
################################################################################
################################################################################
if __name__ == "__main__":
    datagetter = SntpDataGetter()
    datagetter.execute()
