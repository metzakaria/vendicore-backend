import base64
import requests
import hashlib
import logging
from datetime import datetime
import bcrypt
from apps.provider.base import BaseProvider

logger = logging.getLogger(__name__)

"""
******************************************
********* Provider: CreditSwitch **********
******************************************

This service is for CreditSwitch Provider
to be able to send Airtime and Data purchase 
to the provider

"""
class CreditswitchProviderService(BaseProvider):
    def __init__(self, provider_account, merchant_ref=None, receiver_phone=None, amount=None, product_code=None, data_code=None):
        super().__init__(provider_account)
        self.login_id = self.get_config_value('login_id', '')
        self.public_key = self.get_config_value('public_key', '')
        self.private_key = self.get_config_value('private_key', '')
        self.base_url = "https://portal.creditswitch.com"
        self.receiver_phone = receiver_phone
        self.amount = amount
        self.product_code = product_code
        self.data_code = data_code
        self.merchant_ref = merchant_ref


    # ------------------------------------------------------------------------
    # Utility Methods
    # ------------------------------------------------------------------------

    def _get_service_id(self):
        """Get service ID based on product code."""
        if "MTN" in self.product_code:
            return "D04D" if "DATA" in self.product_code else "A04E"
        elif "GLO" in self.product_code:
            return "D03D" if "DATA" in self.product_code else "A03E"
        elif "AIRTEL" in self.product_code:
            return "D01D" if "DATA" in self.product_code else "A01E"
        elif "9MOBILE" in self.product_code:
            return "D02D" if "DATA" in self.product_code else "A02E"
        else:
            return "A04E"  # Default to MTN airtime

    def _generate_checksum(self, payload):
        """Generate checksum for CreditSwitch API."""
        # Create string from payload values in specific order
        checksum_string = f"{self.login_id}|{self.merchant_ref}|{self._get_service_id()}|{self.amount}|{self.private_key}|{self.receiver_phone}"
        concatBytes = checksum_string.encode("utf-8")[:72]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(concatBytes, salt)
        checksum = base64.b64encode(hashed).decode("utf-8")
        return checksum

    def _get_headers(self):
        return {
            "Content-Type": "application/json"
        }

    def _send_json(self, url: str, payload: dict = None, method: str = "POST", headers: dict = None, log_prefix: str = "PROVIDER"):
        """Override to return Creditswitch-specific error format."""
        try:
            logger.info(f"RAW CREDITSWITCH REQUEST PAYLOAD:::{payload} :::: URL::{url}")

            if method.upper() == "GET":
                resp = self.session.get(url, headers=headers, verify=self.verify_ssl, timeout=self.timeout)
            else:
                resp = self.session.post(url, json=payload, headers=headers, verify=self.verify_ssl, timeout=self.timeout)
            
            logger.info(f"RAW CREDITSWITCH RESPONSE:::{resp.text}")
            return resp.json()

        except requests.Timeout:
            logger.error("FAILED CREDITSWITCH REQUEST TIMEOUT")
            return {"statusCode": "80", "statusDescription": f"Request timeout after {self.timeout} seconds"}
                
        except Exception as e:
            logger.exception(f"FAILED CREDITSWITCH REQUEST:, REASON::{e}")
            return {"statusCode": "90", "statusDescription": str(e)}

    def _map_response(self, body: dict):
        """Normalize response for your platform."""
        status_code = body.get("statusCode", "90")
        message = body.get("statusDescription", "")
        provider_ref = body.get("tranxReference", "")

        response = {
            "responseCode": status_code,
            "responseMessage": message,
            "provider_ref": provider_ref,
            "provider_avail_bal": body.get("balance", "0"),
        }

        # Status mapping rules
        if status_code == "00":
            response["responseCode"] = "00"
            response["responseMessage"] = "Successful"
        elif status_code in ["C001", "C04"]:
            response["responseCode"] = "80"
            response["responseMessage"] = "Transaction pending"
        return response


    # ------------------------------------------------------------------------
    # Payload Builders
    # ------------------------------------------------------------------------

    def _payload_airtime(self):
        current_date = datetime.now().isoformat()
        payload = {
            "loginId": self.login_id,
            "key": self.public_key,
            "requestId": self.merchant_ref,
            "serviceId": self._get_service_id(),
            "amount": str(self.amount) if self.amount else None,
            "recipient": self.receiver_phone,
            "date": current_date
        }
        payload["checksum"] = self._generate_checksum(payload)
        return payload

    def _payload_data(self):
        current_date = datetime.now().isoformat()
        payload = {
            "loginId": self.login_id,
            "key": self.public_key,
            "requestId": self.merchant_ref,
            "serviceId": self._get_service_id(),
            "amount": str(self.amount) if self.amount else None,
            "productId": self.data_code,
            "recipient": self.receiver_phone,
            "date": current_date
        }
        payload["checksum"] = self._generate_checksum(payload)
        return payload



    # ------------------------------------------------------------------------
    # Main Methods
    # ------------------------------------------------------------------------

    def send_request(self):
        # Determine if this is airtime or data based on product_code
        if "VTU" in self.product_code or "AIRTIME" in self.product_code:
            payload = self._payload_airtime()
            url = f"{self.base_url}/api/v1/mvend"
        else:
            payload = self._payload_data()
            url = f"{self.base_url}/api/v1/dvend"
        
        headers = self._get_headers()
        body = self._send_json(url, payload, headers=headers, log_prefix="CREDITSWITCH")
        return self._map_response(body)

    def requery(self):
        url = f"{self.base_url}/api/v1/requery?loginId={self.login_id}&key={self.public_key}&requestId={self.merchant_ref}&serviceId={self._get_service_id()}"
        headers = self._get_headers()
        body = self._send_json(url, method="GET", headers=headers, log_prefix="CREDITSWITCH")
        return self._map_response(body)

    def get_balance(self):
        # CreditSwitch may not have a balance endpoint, return default response
        return {
            "responseCode": "90",
            "provider_avail_bal": "0",
            "responseMessage": "Balance check not available for this provider",
        }