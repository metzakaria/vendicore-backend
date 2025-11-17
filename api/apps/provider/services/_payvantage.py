import requests
import logging
import random

from apps.provider.base import BaseProvider

logger = logging.getLogger(__name__)


"""
******************************************
********* Provider: PAYVANTAGE **********
******************************************

This service is for Payvantage Provider
to be able to send Data purchase to the provider
using their REST API

"""
class PayvantageProviderService(BaseProvider):
    def __init__(self, provider_account, receiver_phone=None, amount=None, product_code="", plan_code=""):
        super().__init__(provider_account)
        self.api_key = self.get_config_value('api_key', '')
        self.client_id = self.get_config_value('client_id', '')
        self.base_url = self.get_config_value('base_url', '')
        self.receiver_phone = receiver_phone
        self.amount = amount
        self.product_code = product_code
        # Use plan_code if provided, otherwise try to map from product_code
        self.plan_code = plan_code or self._get_plan_code_from_product(product_code)

    def _get_plan_code_from_product(self, product_code):
        """Map product codes to default plan codes if needed."""
        # This is a fallback mapping - ideally plan_code should be passed explicitly
        default_plans = {
            "MTNDATA": "1005",  # 2GB Monthly Plan
            "GLODATA": "2005",  # Example GLO plan
            "AIRTELDATA": "3005",  # Example Airtel plan
            "9MOBILEDATA": "4005",  # Example 9Mobile plan
        }
        return default_plans.get(product_code, "1005")

    def send_request(self):
        """Send airtime or data vending request to Payvantage provider."""
        response = {}
        try:
            # Generate unique transaction ID
            transaction_id = f"{random.randint(10000, 99999)}-{self.generate_sequence()}"
            
            # Determine if this is airtime or data based on product_code
            if "VTU" in self.product_code or "AIRTIME" in self.product_code:
                return self._send_airtime_request(transaction_id)
            else:
                return self._send_data_request(transaction_id)
                
        except Exception as e:
            logger.error(f"PAYVANTAGE REQUEST FAILED: {e}", exc_info=True)
            return {
                "responseCode": "90",
                "provider_ref": None,
                "responseMessage": str(e),
                "provider_avail_bal": "0"
            }

    def _send_airtime_request(self, transaction_id):
        """Send airtime vending request."""
        network = self._get_network_from_product_code()
        
        payload = {
            "amount": str(self.amount // 100),  # Convert from kobo to naira
            "network": network,
            "phonenumber": self.receiver_phone,
            "transaction_id": transaction_id
        }
        
        headers = {
            "x-api-key": self.api_key,
            "client-id": self.client_id,
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/service/api/single_airtime_direct_vending"
        
        logger.info(f"PAYVANTAGE AIRTIME REQUEST: {payload}")
        
        resp = requests.post(
            url,
            json=payload,
            headers=headers,
            verify=self.verify_ssl,
            timeout=self.timeout
        )
        
        logger.info(f"PAYVANTAGE AIRTIME RESPONSE: {resp.text}")
        return self._process_response(resp.json(), transaction_id)

    def _send_data_request(self, transaction_id):
        """Send data vending request."""
        payload = {
            "plan_code": self.plan_code,
            "phonenumber": self.receiver_phone,
            "transaction_id": transaction_id
        }
        
        headers = {
            "x-api-key": self.api_key,
            "client-id": self.client_id,
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/service/api/single_data_direct_vending"
        
        logger.info(f"PAYVANTAGE DATA REQUEST: {payload}")
        
        resp = requests.post(
            url,
            json=payload,
            headers=headers,
            verify=self.verify_ssl,
            timeout=self.timeout
        )
        
        logger.info(f"PAYVANTAGE DATA RESPONSE: {resp.text}")
        return self._process_response(resp.json(), transaction_id)

    def _process_response(self, json_resp, transaction_id):
        """Process API response and map to standard format."""
        response = {}
        status_code = json_resp.get("status_code", "100")
        
        if status_code == "200":
            response["responseCode"] = "00"
            response["responseMessage"] = "Successful"
        elif status_code == "300":
            response["responseCode"] = "07"
            response["responseMessage"] = "Duplicate transaction"
        elif status_code == "500":
            response["responseCode"] = "01"
            response["responseMessage"] = "Transaction failed"
        elif status_code == "501":
            response["responseCode"] = "02"
            response["responseMessage"] = "Transaction pending"
        elif status_code == "3":
            response["responseCode"] = "08"
            response["responseMessage"] = "Invalid request"
        else:
            response["responseCode"] = "90"
            response["responseMessage"] = json_resp.get("message", "Unknown error")
        
        response["provider_ref"] = json_resp.get("reference", transaction_id)
        response["provider_avail_bal"] = "0"
        
        return response

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

    def get_data_packages(self, network):
        """Get available data packages for a specific network."""
        try:
            payload = {"network": network}
            
            headers = {
                "x-api-key": self.api_key,
                "client-id": self.client_id,
                "Content-Type": "application/json"
            }
            
            url = f"{self.base_url}/service/api/get-packages"
            
            resp = requests.post(
                url,
                json=payload,
                headers=headers,
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            
            json_resp = resp.json()
            
            if json_resp.get("status_code") == "0":
                return {
                    "success": True,
                    "packages": json_resp.get("result", [])
                }
            else:
                return {
                    "success": False,
                    "message": json_resp.get("message", "Failed to get packages")
                }
                
        except Exception as e:
            logger.error(f"PAYVANTAGE GET PACKAGES FAILED: {e}", exc_info=True)
            return {
                "success": False,
                "message": str(e)
            }

    def requery(self, transaction):
        """Requery transaction status from Payvantage provider."""
        try:
            # Determine service code based on transaction type
            service_code = "100" if "VTU" in transaction.product_code else "200"  # 100 for airtime
            
            payload = {
                "service_code": service_code,
                "transaction_id": transaction.provider_ref or transaction.reference
            }
            
            headers = {
                "x-api-key": self.api_key,
                "client-id": self.client_id,
                "Content-Type": "application/json"
            }
            
            url = f"{self.base_url}/check_transaction_status"
            
            resp = requests.post(
                url,
                json=payload,
                headers=headers,
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            
            json_resp = resp.json()
            
            if json_resp.get("status_code") == "200":
                result = json_resp.get("result", {})
                if result.get("status_code") == "200":
                    return {
                        "responseCode": "00",
                        "responseMessage": "Successful",
                        "provider_ref": transaction.provider_ref,
                        "provider_avail_bal": "0"
                    }
            
            return {
                "responseCode": "01",
                "responseMessage": json_resp.get("message", "Transaction not found"),
                "provider_ref": transaction.provider_ref,
                "provider_avail_bal": "0"
            }
            
        except Exception as e:
            logger.error(f"PAYVANTAGE REQUERY FAILED: {e}", exc_info=True)
            return {
                "responseCode": "90",
                "responseMessage": str(e),
                "provider_ref": transaction.provider_ref,
                "provider_avail_bal": "0"
            }
