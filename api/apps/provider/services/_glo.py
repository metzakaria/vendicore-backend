import logging
import re
import requests

from apps.provider.base import BaseProvider
from config.response_codes import SUCCESS, INVALID_MSISDN, PENDING, FAILED, NOT_IMPLEMENTED, RESPONSE_MESSAGES

logger = logging.getLogger(__name__)


"""
******************************************
*********** Provider: GLO   **************
******************************************

This service is for GLO Nigeria Provider
to be able to send Airtime and Data purchase 
to the  provider

"""
class GloProviderService(BaseProvider):
    def __init__(self, provider_account, merchant_ref=None, receiver_phone=None, amount=None, product_code=None, data_code=None):
        super().__init__(provider_account)
        self.url = "http://41.203.65.10:8913/topupservice/service?wsdl"
        self.userId = self.get_config_value('user_id', '')
        self.password = self.get_config_value('password', '')
        self.resellerId = self.get_config_value('reseller_id', '')
        self.clientId = self.get_config_value('client_id', '')
        self.receiver_phone = receiver_phone
        self.amount = amount
        self.data_code = data_code
        self.product_code = product_code
        self.merchant_ref = merchant_ref

    # ------------------------------------------------------------------------
    # Main Methods
    # ------------------------------------------------------------------------
    def send_request(self):
        """Send request to GLO provider."""
        response = {}
        try:
            #payload for airtime vending
            payload = self._generate_payload(self.receiver_phone, self.amount, self.data_code, self.product_code)
            header = {
                "Content-Type": "text/xml"
            }
            
            json_resp = self._send_xml(self.url, payload, header, log_prefix="GLO")
            
            if json_resp is None:
                response["responseCode"] = PENDING
                response["provider_ref"] = None
                response["responseMessage"] = f"Request timeout after {self.timeout} seconds"
                response["provider_avail_bal"] = "0"
                return response

            logger.info(f"JSON FORMATTED GLO RESPONSE :::{json_resp}")

            body = json_resp["soap:Envelope"]["soap:Body"]["ns2:requestTopupResponse"]["return"]
            response["responseCode"] = body["resultCode"]
            response["responseMessage"] = body["resultDescription"]
            response["provider_ref"] = body["ersReference"]
            response["provider_avail_bal"] = body["senderPrincipal"]["accounts"]["account"]["balance"]["value"]
            
            if body["resultCode"] == "0":
                response["responseCode"] = SUCCESS
                response["responseMessage"] = RESPONSE_MESSAGES[SUCCESS]
            elif body["resultCode"] == "94":  # Invalid phone number
                response["responseCode"] = INVALID_MSISDN
                response["responseMessage"] = RESPONSE_MESSAGES[INVALID_MSISDN]
                
        except Exception as e:
            logger.error(f"FAILED GLO REQUEST:, REASON::{e}", exc_info=True)
            response["responseCode"] = FAILED
            response["provider_ref"] = None
            response["responseMessage"] = str(e)
            response["provider_avail_bal"] = "0"
        
        return response

    def _generate_payload(self, receiver_phone, amount, data_code, product_code):
        """Generate payload for GLO request."""
        payload = ""
        try:
            if product_code == "GLOVTU":
                payload = f'''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ext="http://external.interfaces.ers.seamless.com/">
                <soapenv:Header/>
                <soapenv:Body>
                <ext:requestTopup>
                <!--Optional:-->
                <context>
                <!--Optional:-->
                <channel>WSClient</channel>
                <!--Optional:-->
                <clientComment>test xml for ers</clientComment>
                <!--Optional:-->
                <clientId>{self.clientId}</clientId>
                <!--Optional:-->
                <clientReference>{self.generate_sequence()}</clientReference>
                <clientRequestTimeout>500</clientRequestTimeout>
                <!--Optional:-->
                <initiatorPrincipalId>
                <!--reseller id for parent:-->
                <id>{self.resellerId}</id>
                <!--Optional:-->
                <type>RESELLERUSER</type>
                <!--Optional:-->
                <userId>{self.userId}</userId>
                </initiatorPrincipalId>
                <!--password for parent:-->
                <password>{self.password}</password>
                </context>
                <!--Optional:-->
                <senderPrincipalId>
                <!--reseleer id for parent:-->
                <id>{self.resellerId}</id>
                <!--Optional:-->
                <type>RESELLERUSER</type>
                <!--user for the reseller:-->
                <userId>{self.userId}</userId>
                </senderPrincipalId>
                <!--Optional:-->
                <topupPrincipalId>
                <!--user to be topup:-->
                <id>{receiver_phone}</id>
                <!--Optional:-->
                <type>SUBSCRIBERMSISDN</type>
                <!--Optional:-->
                <userId>?</userId>
                </topupPrincipalId>
                <!--Optional:-->
                <senderAccountSpecifier>
                <!--reselleer id for parent:-->
                <accountId>{self.resellerId}</accountId>
                <!--Optional:-->
                <accountTypeId>RESELLER</accountTypeId>
                </senderAccountSpecifier>
                <!--Optional:-->
                <topupAccountSpecifier>
                <!--user to be toped up:-->
                <accountId>{receiver_phone}</accountId>
                <!--Optional:-->
                <accountTypeId>AIRTIME</accountTypeId>
                </topupAccountSpecifier>
                <!--Optional:-->
                <productId>TOPUP</productId>
                <!--Optional:-->
                <amount>
                <!--currency to be toped up:-->
                <currency>NGN</currency>
                <!--amount to be toped up:-->
                <value>{amount}</value>
                </amount>
                </ext:requestTopup>
                </soapenv:Body>
                </soapenv:Envelope>
                '''
            elif self.product_code=="GLODATA":
                payload = f'''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ext="http://external.interfaces.ers.seamless.com/">
                <soapenv:Header/>
                <soapenv:Body>
                <ext:requestTopup>
                <!--Optional:-->
                <context>
                <!--Optional:-->
                <channel>WSClient</channel>
                <!--Optional:-->
                <clientComment>test</clientComment>
                <!--Optional:-->
                <clientId>{self.clientId}</clientId>
                <!--Optional:-->
                <prepareOnly>false</prepareOnly>
                <!--Optional:-->
                <clientReference>{self.generate_sequence()}</clientReference>
                <clientRequestTimeout>500</clientRequestTimeout>
                <!--Optional:-->
                <initiatorPrincipalId>
                <id>{self.resellerId}</id>
                <type>RESELLERUSER</type>
                <userId>{self.userId}</userId>
                </initiatorPrincipalId>
                <password>{self.password}</password>
                <!--Optional:-->
                <transactionProperties>
                <!--Zero or more repetitions:-->
                <entry>
                <!--Optional:-->
                <key>TRANSACTION_TYPE</key>
                <!--Optional:-->
                <value>PRODUCT_RECHARGE</value>
                </entry>
                </transactionProperties>
                </context>
                <!--Optional:-->
                <senderPrincipalId>
                <!--Optional:-->
                <id>{self.resellerId}</id>
                <!--Optional:-->
                <type>RESELLERUSER</type>
                <!--Optional:-->
                <userId>{self.userId}</userId>
                </senderPrincipalId>
                <!--Optional:-->
                <topupPrincipalId>
                <!--Optional:-->
                <id>{receiver_phone}</id>
                <!--Optional:-->
                <type>SUBSCRIBERMSISDN</type>
                <!--Optional:-->
                <userId></userId>
                </topupPrincipalId>
                <!--Optional:-->
                <senderAccountSpecifier>
                <!--Optional:-->
                <accountId>{self.resellerId}</accountId>
                <!--Optional:-->
                <accountTypeId>RESELLER</accountTypeId>
                </senderAccountSpecifier>
                <!--Optional:-->
                <topupAccountSpecifier>
                <!--Optional:-->
                <accountId>{receiver_phone}</accountId>
                <!--Optional:-->
                <accountTypeId>DATA_BUNDLE</accountTypeId>
                </topupAccountSpecifier>
                <!--Optional:-->
                <productId>{data_code}</productId>
                <!--Optional:-->
                <amount>
                <!--Optional:-->
                <currency>NGN</currency>
                <!--Optional:-->
                <value>{amount}</value>
                </amount>
                </ext:requestTopup>
                </soapenv:Body>
                </soapenv:Envelope>
                '''
          
        except Exception as e:
            logger.error(f"FAILED GLO GENERATE PAYLOAD:, REASON::{e}")
        payload = re.sub(r">\s+<", "><", payload)
        return payload

    def requery(self, transaction):
        """Requery transaction status from GLO provider."""
        # TODO: Implement requery logic for GLO
        return {
            "responseCode": NOT_IMPLEMENTED,
            "responseMessage": RESPONSE_MESSAGES[NOT_IMPLEMENTED],
            "provider_ref": None,
            "provider_avail_bal": "0"
        }

    def get_balance(self):
        """Get balance from GLO provider."""
        # TODO: Implement balance query logic for GLO
        return {
            "responseCode": NOT_IMPLEMENTED,
            "provider_avail_bal": "0",
            "responseMessage": "Balance query not implemented"
        }