import requests
import datetime
import xmltodict
import logging
import re

from apps.provider.base import BaseProvider

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
    def __init__(self, provider_account, receiver_phone=None, amount=None, product_code=None):
        super().__init__(provider_account)
        self.url = "https://172.24.4.21:4443/pretups/C2SReceiver?REQUEST_GATEWAY_CODE=Sonite&REQUEST_GATEWAY_TYPE=EXTGW&LOGIN=Sonite_ltd&PASSWORD=f7d461edffe490ec67ea65e3df934ed2&SOURCE_TYPE=EXTGW&SERVICE_PORT=191"
        self.login_pin = self.get_config_value('login_pin', '')
        self.receiver_phone = receiver_phone
        self.amount = amount
        self.product_code = product_code or "AIRTELVTU"

    def extract_balance(self, message):
        """Extract available balance from message."""
        amount_pattern = r"balance is (\d+(?:\.\d+)?) NGN"
        match = re.search(amount_pattern, message)
        if match:
            return match.group(1)
        return ""

    def generate_sequence(self):
        """Generate sequence number for Airtel (with SONITE prefix)."""
        return "SONITE_" + str(super().generate_sequence())

    def send_request(self):
        """Send request to Airtel provider."""
        response = {}
        try:
            payload = self._generate_payload(self.receiver_phone, self.amount, self.product_code)
            header = {
                "Content-Type": "text/xml",
                "Content-length": str(len(payload))
            }
            logger.info(f"RAW AIRTEL REQUEST PAYLOAD:::{payload} :::: HEADER::{header} :::: URL::{self.url}")
            
            resp = requests.post(
                self.url,
                data=payload,
                headers=header,
                verify=self.verify_ssl,
                timeout=self.timeout
            ).content
            logger.info(f"RAW AIRTEL RESPONSE:::{resp}")
            json_resp = xmltodict.parse(resp)
            logger.info(f"JSON FORMATTED AIRTEL RESPONSE :::{json_resp}")

            body = json_resp["COMMAND"]
            response["responseCode"] = body["TXNSTATUS"]
            response["responseMessage"] = body["MESSAGE"]
            response["provider_ref"] = body["TXNID"]
            response["provider_avail_bal"] = self.extract_balance(body["MESSAGE"])
            
            if body["TXNSTATUS"] == "200":
                response["responseCode"] = "00"
            elif body["TXNSTATUS"] == "17017":
                response["responseCode"] = "08"
                response["responseMessage"] = "Invalid MSISDN"
                
        except requests.Timeout as e:
            logger.error(f"FAILED AIRTEL REQUEST TIMEOUT:: REASON::{e}")
            response["responseCode"] = "80"
            response["provider_ref"] = None
            response["responseMessage"] = f"Request timeout after {self.timeout} seconds"
            response["provider_avail_bal"] = "0"
        except Exception as e:
            logger.error(f"FAILED AIRTEL REQUEST:, REASON::{e}", exc_info=True)
            response["responseCode"] = "90"
            response["provider_ref"] = None
            response["responseMessage"] = str(e)
            response["provider_avail_bal"] = "0"
        
        return response

    def _generate_payload(self, receiver_phone, amount, product_code):
        """Generate payload for Airtel request."""
        datenow = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        payload = ""
        try:
            if product_code == "AIRTELVTU":
                payload = f'''<?xml version=\"1.0\"?><!DOCTYPE COMMAND PUBLIC \"-//Ocam//DTD XML Command 1.0//EN\" \"xml/command.dtd\"><COMMAND><TYPE>EXRCTRFREQ</TYPE><DATE>{datenow}</DATE><EXTNWCODE>NG</EXTNWCODE><MSISDN>{self.vend_sim}</MSISDN><PIN>{self.login_pin}</PIN><LOGINID></LOGINID><PASSWORD></PASSWORD><EXTCODE></EXTCODE><EXTREFNUM>{self.generate_sequence()}</EXTREFNUM><MSISDN2>{receiver_phone}</MSISDN2><AMOUNT>{amount}</AMOUNT><LANGUAGE1>1</LANGUAGE1><LANGUAGE2>1</LANGUAGE2><SELECTOR>1</SELECTOR></COMMAND>'''
            elif product_code == "AIRTELDATA":
                payload = f'''<?xml version=\"1.0\"?><!DOCTYPE COMMAND PUBLIC \"-//Ocam//DTD XML Command1.0//EN\" \"xml/command.dtd\"><COMMAND><TYPE>VASSELLREQ</TYPE><DATE>{datenow}</DATE><EXTNWCODE>NG</EXTNWCODE><MSISDN>{self.vend_sim}</MSISDN><PIN>{self.login_pin}</PIN><LOGINID></LOGINID><PASSWORD></PASSWORD><EXTCODE></EXTCODE><EXTREFNUM></EXTREFNUM><SUBSMSISDN>{receiver_phone}</SUBSMSISDN><AMT>{amount}</AMT><SUBSERVICE>7</SUBSERVICE></COMMAND>'''
        except Exception as e:
            logger.error(f"FAILED AIRTEL GENERATE PAYLOAD:, REASON::{e}")
        return payload

    def requery(self, transaction):
        """Requery transaction status from Airtel provider."""
        # TODO: Implement requery logic for Airtel
        return {
            "responseCode": "99",
            "responseMessage": "Requery not implemented",
            "provider_ref": None,
            "provider_avail_bal": "0"
        }


    
