import requests
import hashlib
import logging
import random
from datetime import datetime

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
    def __init__(self, provider_account, receiver_phone=None, amount=None, product_code="", product_id=""):
        super().__init__(provider_account)
        self.login_id = self.get_config_value('login_id', '')
        self.public_key = self.get_config_value('public_key', '')
        self.private_key = self.get_config_value('private_key', '')
        self.base_url = self.get_config_value('base_url', '')
        self.receiver_phone = receiver_phone
        self.amount = amount
        self.product_code = product_code
        self.product_id = product_id

    def _generate_checksum(self, payload):
        """Generate checksum for CreditSwitch API."""
        # Create string from payload values in specific order
        checksum_string = f"{payload['loginId']}{payload['key']}{payload['requestId']}"
        if 'serviceId' in payload:
            checksum_string += payload['serviceId']
        checksum_string += f"{payload['amount']}{payload['recipient']}{payload['date']}"
        if 'productId' in payload:
            checksum_string += payload['productId']
        checksum_string += self.private_key
        
        # Generate SHA256 hash
        return hashlib.sha256(checksum_string.encode()).hexdigest()

    def _get_service_id(self):
        """Get service ID based on product code."""
        if "MTN" in self.product_code:
            return "D04D" if "DATA" in self.product_code else "A04E"
        elif "GLO" in self.product_code:
            return "D04G" if "DATA" in self.product_code else "A04G"
        elif "AIRTEL" in self.product_code:
            return "D04A" if "DATA" in self.product_code else "A04A"
        elif "9MOBILE" in self.product_code:
            return "D04N" if "DATA" in self.product_code else "A04N"
        else:
            return "A04E"  # Default to MTN airtime

    def send_request(self):
        """Send airtime or data vending request to CreditSwitch provider."""
        try:
            # Determine if this is airtime or data
            if "VTU" in self.product_code or "AIRTIME" in self.product_code:
                return self._send_airtime_request()
            else:
                return self._send_data_request()
                
        except Exception as e:
            logger.error(f"CREDITSWITCH REQUEST FAILED: {e}", exc_info=True)
            return {
                "responseCode": "90",
                "provider_ref": None,
                "responseMessage": str(e),
                "provider_avail_bal": "0"
            }

    def _send_airtime_request(self):
        """Send airtime vending request."""
        request_id = str(random.randint(100000000000, 999999999999))
        current_date = datetime.now().isoformat()
        
        payload = {
            "loginId": self.login_id,
            "key": self.public_key,
            "requestId": request_id,
            "serviceId": self._get_service_id(),
            "amount": self.amount // 100,  # Convert from kobo to naira
            "recipient": self.receiver_phone,
            "date": current_date
        }
        
        payload["checksum"] = self._generate_checksum(payload)
        
        url = f"{self.base_url}/api/v1/mvend"
        
        logger.info(f"CREDITSWITCH AIRTIME REQUEST: {payload}")
        
        resp = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            verify=self.verify_ssl,
            timeout=self.timeout
        )
        
        logger.info(f"CREDITSWITCH AIRTIME RESPONSE: {resp.text}")
        return self._process_response(resp.json(), request_id)

    def _send_data_request(self):
        """Send data vending request."""
        request_id = str(random.randint(100000000000, 999999999999))
        current_date = datetime.now().isoformat()
        
        payload = {
            "loginId": self.login_id,
            "key": self.public_key,
            "requestId": request_id,
            "serviceId": self._get_service_id(),
            "amount": self.amount // 100,  # Convert from kobo to naira
            "productId": self.product_id,
            "recipient": self.receiver_phone,
            "date": current_date
        }
        
        payload["checksum"] = self._generate_checksum(payload)
        
        url = f"{self.base_url}/api/v1/dvend"
        
        logger.info(f"CREDITSWITCH DATA REQUEST: {payload}")
        
        resp = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            verify=self.verify_ssl,
            timeout=self.timeout
        )
        
        logger.info(f"CREDITSWITCH DATA RESPONSE: {resp.text}")
        return self._process_response(resp.json(), request_id)

    def get_data_plans(self, service_id):
        """Get available data plans for a service."""
        try:
            payload = {
                "loginId": self.login_id,
                "serviceId": service_id,
                "key": self.public_key
            }
            
            url = f"{self.base_url}/api/v1/mdataplans"
            
            resp = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            
            return resp.json()
            
        except Exception as e:
            logger.error(f"CREDITSWITCH GET DATA PLANS FAILED: {e}", exc_info=True)
            return {"success": False, "message": str(e)}

    def _process_response(self, json_resp, request_id):
        """Process API response and map to standard format."""
        response = {}
        
        # CreditSwitch response format may vary - adapt based on actual API response
        if json_resp.get("status") == "success" or json_resp.get("responseCode") == "00":
            response["responseCode"] = "00"
            response["responseMessage"] = "Successful"
        elif json_resp.get("status") == "pending":
            response["responseCode"] = "02"
            response["responseMessage"] = "Transaction pending"
        else:
            response["responseCode"] = "01"
            response["responseMessage"] = json_resp.get("message", "Transaction failed")
        
        response["provider_ref"] = json_resp.get("transactionId", request_id)
        response["provider_avail_bal"] = json_resp.get("balance", "0")
        
        return response

    def requery(self, transaction):
        """Requery transaction status from CreditSwitch provider."""
        # CreditSwitch requery implementation would go here
        # Based on their requery endpoint documentation
        return {
            "responseCode": "99",
            "responseMessage": "Requery not implemented",
            "provider_ref": transaction.provider_ref,
            "provider_avail_bal": "0"
        }
