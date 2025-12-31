import logging
import re
import requests

from apps.provider.base import BaseProvider
from config.response_codes import SUCCESS, INVALID_MSISDN, PENDING, FAILED, NOT_IMPLEMENTED, RESPONSE_MESSAGES

logger = logging.getLogger(__name__)


"""
******************************************
**** Provider: 9MOBILE / ETISALAT  *******
******************************************

This service is for 9Mobile/Etisalat Nigeria Provider
to be able to send Airtime and Data purchase 
to the  provider

"""
class EtisalatProviderService(BaseProvider):
    def __init__(self, provider_account, merchant_ref=None, receiver_phone=None, amount=None, product_code="9MOBILEVTU"):
        super().__init__(provider_account)
        self.url = "https://10.158.8.33:9090/EVC/SinglePointFulfilment/EVCPinlessInterfaceEndpoint"
        self.username = self.get_config_value('username', '')
        self.password = self.get_config_value('password', '')
        self.auth_key = self.get_config_value('auth_key', '')
        self.auth_token = self.get_config_value('auth_token', '')
        self.receiver_phone = receiver_phone
        self.amount = amount
        self.product_code = product_code
        # Calculate recharge type
        self.recharge_type = "001" if product_code == "9MOBILEVTU" else "991"
        self.merchant_ref = merchant_ref

    # ------------------------------------------------------------------------
    # Main Methods
    # ------------------------------------------------------------------------
    def extract_balance(self, message):
        """Extract available balance from message."""
        amount_pattern = r"balance is (\d+(?:\.\d+)?) NGN"
        match = re.search(amount_pattern, message)
        if match:
            return match.group(1)
        return "0"

    def send_request(self):
        """Send request to 9Mobile/Etisalat provider."""
        # Convert amount to kobo (multiply by 100)
        amount_kobo = str(int(float(self.amount) * 100)) if self.amount else "0"
        
        response = {}
        try:
            payload = f'''<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:com=\"http://sdf.cellc.net/commonDataModel\">\n<soapenv:Header/>\n<soapenv:Body>\n<SDF_Data xmlns=\"http://sdf.cellc.net/commonDataModel\" xmlns:SOAP-ENV=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">\n<header>\n<processTypeID>7002</processTypeID>\n<externalReference>{self.generate_sequence()}</externalReference>\n<sourceID>{self.vend_sim}</sourceID>\n<username>{self.username}</username>\n<password>{self.password}</password>\n<processFlag>1</processFlag>\n</header>\n<parameters>\n<parameter name=\"RechargeType\">{self.recharge_type}</parameter>\n<parameter name=\"MSISDN\">{self.receiver_phone}</parameter>\n<parameter name=\"Amount\">{amount_kobo}</parameter>\n<parameter name=\"Channel_ID\">2ENG0011</parameter>\n</parameters>\n</SDF_Data>\n</soapenv:Body>\n</soapenv:Envelope>'''
 
            header = {
                "Content-Type": "text/xml;charset=\"utf-8\"",
                "Accept": "text/xml",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "SOAPAction": "\"http://sdf.cellc.net/process\"",
                "Content-length": str(len(payload)),
                "key": self.auth_key,
                "token": self.auth_token
            }
            
            json_resp = self._send_xml(self.url, payload, header, log_prefix="9MOBILE")
            
            if json_resp is None:
                response["responseCode"] = PENDING
                response["responseMessage"] = f"Request timeout after {self.timeout} seconds"
                response["provider_ref"] = None
                response["provider_avail_bal"] = "0"
                return response

            logger.info(f"JSON FORMATTED 9MOBILE RESPONSE :::{json_resp}")

            body = json_resp["soapenv:Envelope"]["soapenv:Body"]["com:SDF_Data"]["com:result"]
            response["responseCode"] = body["com:statusCode"]
            response["responseMessage"] = body["com:errorDescription"]
            response["provider_ref"] = body["com:instanceId"]
            response["provider_avail_bal"] = "0"
            
            if body["com:statusCode"] == "0":
                response["responseCode"] = SUCCESS
                response["responseMessage"] = RESPONSE_MESSAGES[SUCCESS]
            elif body["com:statusCode"] == "2" and 'Insufficient Funds' not in response["responseMessage"]:
                response["responseCode"] = INVALID_MSISDN
                response["responseMessage"] = RESPONSE_MESSAGES[INVALID_MSISDN]
                
        except Exception as e:
            logger.error(f"FAILED 9MOBILE REQUEST:, REASON::{e}", exc_info=True)
            response["responseCode"] = FAILED
            response["responseMessage"] = str(e)
            response["provider_ref"] = None
            response["provider_avail_bal"] = "0"
        
        return response

    def requery(self, transaction):
        """Requery transaction status from 9Mobile/Etisalat provider."""
        # TODO: Implement requery logic for Etisalat
        return {
            "responseCode": NOT_IMPLEMENTED,
            "responseMessage": RESPONSE_MESSAGES[NOT_IMPLEMENTED],
            "provider_ref": None,
            "provider_avail_bal": "0"
        }

    def get_balance(self):
        """Get balance from 9Mobile/Etisalat provider."""
        # TODO: Implement balance query logic for Etisalat
        return {
            "responseCode": NOT_IMPLEMENTED,
            "provider_avail_bal": "0",
            "responseMessage": "Balance query not implemented"
        }
