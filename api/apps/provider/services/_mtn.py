import requests
import xmltodict
import logging
import random

from apps.provider.base import BaseProvider

logger = logging.getLogger(__name__)


"""
******************************************
********* Provider: MTN Nigeria **********
******************************************

This service is for MTN Nigeria Provider
to be able to send Airtime and Data purchase 
to the provider

"""
class MTNNProviderService(BaseProvider):
    def __init__(self, provider_account, receiver_phone=None, amount=None, tariff_type_id="1"):
        super().__init__(provider_account)
        self.url = "https://ershostif.mtn.ng/axis2/services/HostIFService"
        username = self.get_config_value('username', '')
        password = self.get_config_value('password', '')
        self.auth_token = f"{username}:{password}"
        self.receiver_phone = receiver_phone
        self.amount = amount
        self.tariff_type_id = tariff_type_id

    def send_request(self):
        """Send request to MTN provider."""
        response = {}
        try:
            payload = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?><soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://hostif.vtm.prism.co.za/xsd"><soapenv:Header/><soapenv:Body><xsd:vend><xsd:origMsisdn>{self.vend_sim}</xsd:origMsisdn><xsd:destMsisdn>{self.receiver_phone}</xsd:destMsisdn><xsd:amount>{self.amount}</xsd:amount><xsd:sequence>{self.generate_sequence()}</xsd:sequence><xsd:tariffTypeId>{self.tariff_type_id}</xsd:tariffTypeId><xsd:serviceproviderId>1</xsd:serviceproviderId></xsd:vend></soapenv:Body></soapenv:Envelope>'''
            
            header = {
                "Authorization": f"Basic {self.encode_base64(self.auth_token)}",
                "Content-Type": "application/xml",
                "SoapAction": "urn:queryTx",
                "Content-length": str(len(payload)),
                "charset": "UTF-8"
            }
            logger.info(f"RAW MTNN REQUEST PAYLOAD:::{payload}")
            
            resp = requests.post(
                self.url, 
                data=payload, 
                headers=header, 
                verify=self.verify_ssl, 
                timeout=self.timeout
            ).content
            logger.info(f"RAW MTNN RESPONSE:::{resp}")
            json_resp = xmltodict.parse(resp)
            logger.info(f"JSON FORMATTED MTNN RESPONSE :::{json_resp}")

            body = json_resp["SOAP-ENV:Envelope"]["SOAP-ENV:Body"]["xsd:vendResponse"]
            response["responseCode"] = body["xsd:statusId"]
            response["responseMessage"] = body["xsd:responseMessage"]
            try: 
                response["provider_ref"] = body["xsd:txRefId"]
            except Exception:
                response["provider_ref"] = None
            response["provider_avail_bal"] = body.get("xsd:origBalance", "0")
            
            if body["xsd:statusId"] == "0":
                response["responseCode"] = "00"
            elif body["xsd:statusId"] in ["1004", "202"]:  # Invalid phone number
                response["responseCode"] = "08"
                response["responseMessage"] = "Invalid MSISDN"
                
        except requests.Timeout as e:
            logger.error(f"FAILED MTNN REQUEST TIMEOUT:: REASON::{e}")
            response["responseCode"] = "80"
            response["provider_ref"] = None
            response["responseMessage"] = f"Request timeout after {self.timeout} seconds"
        except Exception as e:
            logger.error(f"FAILED MTNN REQUEST:, REASON::{e}", exc_info=True)
            response["responseCode"] = "90"
            response["provider_ref"] = None
            response["responseMessage"] = str(e)
            response["provider_avail_bal"] = "0"
        
        return response

    def requery(self, transaction):
        """Requery transaction status from MTN provider."""
        # TODO: Implement requery logic for MTN
        return {
            "responseCode": "99",
            "responseMessage": "Requery not implemented",
            "provider_ref": None,
            "provider_avail_bal": "0"
        }


