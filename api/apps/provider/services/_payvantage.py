import logging

from apps.provider.base import BaseProvider
from config.response_codes import SUCCESS, PENDING, FAILED, NOT_IMPLEMENTED, TRANSACTION_NOT_FOUND, RESPONSE_MESSAGES

logger = logging.getLogger(__name__)

"""
******************************************
********* Provider: PAYVANTAGE **********
******************************************

This service is for Payvantage Provider
to be able to send Airtime and Data purchase 
to the provider using their REST API

"""
class PayvantageProviderService(BaseProvider):
    def __init__(self, provider_account, merchant_ref=None, receiver_phone=None, amount=None, product_code=None, data_code=None):
        super().__init__(provider_account)
        self.api_key = self.get_config_value('api_key', '')
        self.client_id = self.get_config_value('client_id', '')
        self.base_url = "https://vend-prod.payvantageapi.com"
        self.merchant_ref = merchant_ref
        self.receiver_phone = receiver_phone
        self.amount = amount
        self.product_code = product_code
        self.data_code = data_code


    # ------------------------------------------------------------------------
    # Utility Methods
    # ------------------------------------------------------------------------

    def _get_network_from_product_code(self):
        """Get network name from product code."""
        if "MTN" in self.product_code:
            return "MTN"
        elif "GLO" in self.product_code:
            return "GLO"
        elif "AIRTEL" in self.product_code:
            return "AIRTEL"
        elif "9MOBILE" in self.product_code:
            return "9Mobile"
        else:
            return "MTN"  # Default fallback

    def _get_headers(self):
        return {
            "x-api-key": self.api_key,
            "client-id": self.client_id,
            "Content-Type": "application/json"
        }


    def _map_response(self, body: dict):
        """Normalize response for your platform."""
        status_code = body.get("status_code", "100")
        message = body.get("message", "")
        provider_ref = body.get("reference", "")

        response = {
            "responseCode": status_code,
            "responseMessage": message,
            "provider_ref": provider_ref,
            "provider_avail_bal": "0",
        }

        # Status mapping rules
        if status_code == "200":
            response["responseCode"] = SUCCESS
            response["responseMessage"] = RESPONSE_MESSAGES[SUCCESS]
        elif status_code == "501":
            response["responseCode"] = PENDING
            response["responseMessage"] = RESPONSE_MESSAGES[PENDING]
        return response


    # ------------------------------------------------------------------------
    # Payload Builders
    # ------------------------------------------------------------------------

    def _payload_airtime(self):
        network = self._get_network_from_product_code()
        return {
            "amount": str(self.amount),
            "network": network,
            "phonenumber": self.receiver_phone,
            "transaction_id": self.merchant_ref
        }

    def _payload_data(self):
        return {
            "plan_code": self.data_code,
            "phonenumber": self.receiver_phone,
            "transaction_id": self.merchant_ref
        }
        
    def _payload_requery(self):
            # Determine service code based on transaction type
        service_code = "100" if "VTU" in self.product_code or "AIRTIME" in self.product_code else "200"
        return {
                "service_code": service_code,
                "transaction_id": self.merchant_ref
            }
            

    # ------------------------------------------------------------------------
    # Main Methods
    # ------------------------------------------------------------------------

    def send_request(self):
        # Determine if this is airtime or data based on product_code
        if "VTU" in self.product_code or "AIRTIME" in self.product_code:
            payload = self._payload_airtime()
            url = f"{self.base_url}/service/api/single_airtime_direct_vending"
        else:
            payload = self._payload_data()
            url = f"{self.base_url}/service/api/single_data_direct_vending"
        headers = self._get_headers()
        body = self._send_json(url, payload, headers=headers, log_prefix="PAYVANTAGE")
        return self._map_response(body)

    def requery(self):
        payload = self._payload_requery()
        url = f"{self.base_url}/service/api/check_transaction_status"
        headers = self._get_headers()
        body = self._send_json(url, payload, headers=headers, log_prefix="PAYVANTAGE")

        if body.get("status_code") == "200":
            result = body.get("result", {})
            if result.get("status_code") == "200":
                return {
                    "responseCode": SUCCESS,
                    "responseMessage": RESPONSE_MESSAGES[SUCCESS],
                    "provider_ref": self.merchant_ref,
                    "provider_avail_bal": "0"
                }
            
            return {
                "responseCode": TRANSACTION_NOT_FOUND,
                "responseMessage": body.get("message", RESPONSE_MESSAGES[TRANSACTION_NOT_FOUND]),
                "provider_ref": self.merchant_ref,
                "provider_avail_bal": "0"
            }
            
    def get_balance(self):
        # Payvantage may not have a balance endpoint, return default response
        return {
            "responseCode": FAILED,
            "provider_avail_bal": "0",
            "responseMessage": "Balance check not available for this provider",
        }