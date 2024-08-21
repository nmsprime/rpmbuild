#!/usr/bin/env python3

import base_data_getter

################################################################################
################################################################################
class SmtpDataGetter(base_data_getter.BaseDataGetter):

    implemented_modes = {
        "simple": "_execute_simple",
    }

    implemented_protos = (
        "SMTP",
        "SMTPS",
    )

    status_mapping = {
        "Success": 0,
        "Unknown error": 1,
        "OSError": 2,
        "socket.gaierror": 3,
        "TimeoutError": 4,
        "smtplib.SMTPAuthenticationError": 5,
        "smtplib.SMTPConnectError": 6,
        "smtplib.SMTPDataError": 7,
        "smtplib.SMTPHeloError": 8,
        "smtplib.SMTPNotSupportedError": 9,
        "smtplib.SMTPRecipientsRefused": 10,
        "smtplib.SMTPResponseException": 11,
        "smtplib.SMTPSenderRefused": 12,
        "smtplib.SMTPServerDisconnected": 13,
        "smtplib.SMTPException": 14,
    }

    ############################################################################
    def _execute_simple(self):

        if self.params["proto"] == "SMTP":
            from smtplib import SMTP as TEST_SMTP_CLASS
        elif self.params["proto"] == "SMTPS":
            from smtplib import SMTP_SSL as TEST_SMTP_CLASS

        with TEST_SMTP_CLASS(
            host=self.params["host"],
            port=self.params["port"],
            timeout=self.params["timeout"],
        ) as smtp:
            smtp.noop()

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
    getter = SmtpDataGetter()
    getter.execute()
