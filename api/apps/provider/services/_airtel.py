import datetime
import logging
import re

from apps.provider.base import BaseProvider
from config.response_codes import SUCCESS, INVALID_MSISDN, PENDING, FAILED, RESPONSE_MESSAGES

logger = logging.getLogger(__name__)

"""
******************************************
********* Provider: AIRTEL Nigeria **********
******************************************

This service is for Airtel Nigeria Provider
to be able to send Airtime and Data purchase 
to the  provider

"""
class AirtelProviderService(BaseProvider):
    def __init__(self, provider_account, merchant_ref=None, receiver_phone=None, amount=None, product_code=None, data_code=None):
        super().__init__(provider_account)
        #self.url = "https://172.24.4.21:4443/pretups/C2SReceiver?REQUEST_GATEWAY_CODE=TELKO&REQUEST_GATEWAY_TYPE=EXTGW&LOGIN=pretups&PASSWORD=908cff993002341304d8c732b614ffc0&SOURCE_TYPE=EXTGW&SERVICE_PORT=191"
        self.url = "https://pretupsapi.airtel.com.ng:4443/pretups/C2SReceiver?REQUEST_GATEWAY_CODE=TELKO&REQUEST_GATEWAY_TYPE=EXTGW&LOGIN=pretups&PASSWORD=908cff993002341304d8c732b614ffc0&SOURCE_TYPE=EXTGW&SERVICE_PORT=191"
        self.login_pin = self.get_config_value('login_pin', '')
        self.login_id = self.get_config_value('login_id', '')
        self.password = self.get_config_value('password', '')
        self.receiver_phone = receiver_phone
        self.amount = amount
        self.product_code = product_code or "AIRTELVTU"
        self.merchant_ref = merchant_ref
        self.data_code = data_code


    # ------------------------------------------------------------------------
    # Utility Methods
    # ------------------------------------------------------------------------

    def _extract_balance(self, message: str):
        match = re.search(r"balance is (\d+(?:\.\d+)?) NGN", message or "")
        return match.group(1) if match else ""

    def _header(self, payload):
        return {
            "Content-Type": "text/xml",
            "Content-length": str(len(payload))
        }


    def _map_response(self, body: dict):
        """Normalize response for your platform."""
        status = body.get("TXNSTATUS")
        message = body.get("MESSAGE", "")
        provider_ref = body.get("TXNID")

        response = {
            "responseCode": status,
            "responseMessage": message,
            "provider_ref": provider_ref,
            "provider_avail_bal": self._extract_balance(message),
        }

        # Status mapping rules
        if status == "200":
            response["responseCode"] = SUCCESS
            response["responseMessage"] = RESPONSE_MESSAGES[SUCCESS]
        elif status == "17017":
            response["responseCode"] = INVALID_MSISDN
            response["responseMessage"] = RESPONSE_MESSAGES[INVALID_MSISDN]
        elif status in {"205", "250"}:
            response["responseCode"] = PENDING
            response["responseMessage"] = RESPONSE_MESSAGES[PENDING]
        return response



     # ------------------------------------------------------------------------
    # Payload Builders
    # ------------------------------------------------------------------------

    def _payload_vtu(self):
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return f"""
        <?xml version="1.0"?>
        <!DOCTYPE COMMAND PUBLIC "-//Ocam//DTD XML Command 1.0//EN" "xml/command.dtd">
        <COMMAND>
            <TYPE>EXRCTRFREQ</TYPE>
            <DATE>{now}</DATE>
            <EXTNWCODE>NG</EXTNWCODE>
            <MSISDN>{self.vend_sim}</MSISDN>
            <PIN>{self.login_pin}</PIN>
            <LOGINID>{self.login_id}</LOGINID><PASSWORD>{self.password}</PASSWORD><EXTCODE></EXTCODE>
            <EXTREFNUM>{self.merchant_ref}</EXTREFNUM>
            <MSISDN2>{self.receiver_phone}</MSISDN2>
            <AMOUNT>{self.amount}</AMOUNT>
            <LANGUAGE1>1</LANGUAGE1>
            <LANGUAGE2>1</LANGUAGE2>
            <SELECTOR>1</SELECTOR>
        </COMMAND>
        """.strip()

    def _payload_data(self):
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return f"""
        <?xml version="1.0"?>
        <!DOCTYPE COMMAND PUBLIC "-//Ocam//DTD XML Command1.0//EN" "xml/command.dtd">
        <COMMAND>
            <TYPE>VASSELLREQ</TYPE>
            <DATE>{now}</DATE>
            <EXTNWCODE>NG</EXTNWCODE>
            <MSISDN>{self.vend_sim}</MSISDN>
            <PIN>{self.login_pin}</PIN>
            <LOGINID>{self.login_id}</LOGINID><PASSWORD>{self.password}</PASSWORD><EXTCODE></EXTCODE>
            <EXTREFNUM>{self.merchant_ref}</EXTREFNUM>
            <SUBSMSISDN>{self.receiver_phone}</SUBSMSISDN>
            <AMT>{self.amount}</AMT>
            <SUBSERVICE>7</SUBSERVICE>
        </COMMAND>
        """.strip()

    def _payload_requery(self, merchant_ref):
        return f"""
        <?xml version="1.0"?>
        <!DOCTYPE COMMAND PUBLIC "-//Ocam//DTD XML Command 1.0//EN" "xml/command.dtd">
        <COMMAND>
            <TYPE>EXRCSTATREQ</TYPE>
            <DATE></DATE>
            <EXTNWCODE>NG</EXTNWCODE>
            <MSISDN>{self.vend_sim}</MSISDN>
            <PIN>{self.login_pin}</PIN>
            <LOGINID>{self.login_id}</LOGINID>< PASSWORD>{self.password}</PASSWORD><EXTCODE></EXTCODE>
            <EXTREFNUM>{merchant_ref}</EXTREFNUM>
            <TXNID></TXNID>
            <LANGUAGE1>1</LANGUAGE1>
        </COMMAND>
        """.strip()

    def _payload_balance(self):
        return f"""
        <?xml version="1.0"?>
        <COMMAND>
            <TYPE>EXUSRBALREQ</TYPE>
            <DATE></DATE>
            <EXTNWCODE>NG</EXTNWCODE>
            <MSISDN>{self.vend_sim}</MSISDN>
            <PIN>{self.login_pin}</PIN>
            <LOGINID>{self.login_id}</LOGINID><PASSWORD>{self.password}</PASSWORD><EXTCODE></EXTCODE><EXTREFNUM></EXTREFNUM>
        </COMMAND>
        """.strip()


    # ------------------------------------------------------------------------
    # Main Methods
    # ------------------------------------------------------------------------

    def send_request(self):
        payload = self._payload_vtu() if self.product_code == "AIRTELVTU" else self._payload_data()
        headers = self._header(payload)
        parsed = self._send_xml(self.url, payload, headers, log_prefix="AIRTEL")
        body = parsed.get("COMMAND", {}) if parsed else {"TXNSTATUS": FAILED, "MESSAGE": RESPONSE_MESSAGES[FAILED]}
        return self._map_response(body)

    def requery(self):
        payload = self._payload_requery(self.merchant_ref)
        headers = self._header(payload)
        parsed = self._send_xml(self.url, payload, headers, log_prefix="AIRTEL")
        body = parsed.get("COMMAND", {}) if parsed else {"TXNSTATUS": FAILED, "MESSAGE": RESPONSE_MESSAGES[FAILED]}
        return self._map_response(body)

    def get_balance(self):
        payload = self._payload_balance()
        headers = self._header(payload)
        parsed = self._send_xml(self.url, payload, headers, log_prefix="AIRTEL")
        body = parsed.get("COMMAND", {}) if parsed else {"TXNSTATUS": FAILED, "MESSAGE": RESPONSE_MESSAGES[FAILED]}

        status = body.get("TXNSTATUS", FAILED)
        # Normalize status code
        if status == "200":
            status = SUCCESS
        elif status in {"205", "250", "80"}:
            status = PENDING
        elif status == "90":
            status = FAILED

        return {
            "responseCode": status,
            "provider_avail_bal": body.get("BALANCE", "0"),
            "responseMessage": body.get("MESSAGE", RESPONSE_MESSAGES.get(status, "")),
        }
