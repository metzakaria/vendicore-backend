import abc
import logging
import random
import base64
import requests

logger = logging.getLogger(__name__)

class BaseProvider(abc.ABC):
    def __init__(self, provider_account):
        """
        provider_account: ProviderAccount instance from DB
        provider_account.config: contains credentials, endpoints, etc.
        """
        self.account = provider_account
        self.config = provider_account.config or {}
        self.vend_sim = provider_account.vending_sim or ''
        self.timeout = 10 #self.config.get('timeout', 10)
        self.verify_ssl = self.config.get('verify_ssl', False)
        self.session = requests.Session()

    def generate_sequence(self):
        """Generate a random sequence number for requests."""
        return random.randint(1000000000, 9999999999)

    def encode_base64(self, string_to_encode):
        """Encode a string to base64."""
        encoded_bytes = base64.b64encode(string_to_encode.encode('utf-8'))
        return encoded_bytes.decode('utf-8')

    def get_config_value(self, key, default=None):
        """Get a value from config with optional default."""
        return self.config.get(key, default)

    def _send_json(self, url: str, payload: dict = None, method: str = "POST", headers: dict = None, log_prefix: str = "PROVIDER"):
        """Send JSON request. Returns parsed JSON or error dict."""
        try:
            logger.info(f"RAW {log_prefix} REQUEST PAYLOAD:::{payload} :::: URL::{url} :::: HEADERS::{headers}")

            if method.upper() == "GET":
                resp = self.session.get(url, headers=headers, verify=True, timeout=self.timeout)
            else:
                resp = self.session.post(url, json=payload, headers=headers, verify=True, timeout=self.timeout)
            
            logger.info(f"RAW {log_prefix} RESPONSE:::{resp.text}")
            return resp.json()

        except requests.Timeout:
            logger.error(f"FAILED {log_prefix} REQUEST TIMEOUT")
            return {"status_code": "80", "message": f"Request timeout after {self.timeout} seconds"}

        except Exception as e:
            logger.exception(f"FAILED {log_prefix} REQUEST:, REASON::{e}")
            return {"status_code": "90", "message": str(e)}

    def _send_xml(self, url: str, payload: str, headers: dict = None, log_prefix: str = "PROVIDER"):
        """Send XML request. Returns full parsed XML dict or None on error."""
        try:
            logger.info(f"RAW {log_prefix} REQUEST PAYLOAD:::{payload} :::: URL::{url}")

            resp = self.session.post(url, data=payload, headers=headers, verify=self.verify_ssl, timeout=self.timeout)
            logger.info(f"RAW {log_prefix} RESPONSE:::{resp.content} :::: HEADERS::{headers}")
            
            import xmltodict
            parsed = xmltodict.parse(resp.content)
            return parsed

        except requests.Timeout:
            logger.error(f"FAILED {log_prefix} REQUEST TIMEOUT")
            return None

        except Exception as e:
            logger.exception(f"FAILED {log_prefix} REQUEST:, REASON::{e}")
            return None

    @abc.abstractmethod
    def send_request(self):
        """
        Send request to provider for vending. Must be implemented.
        Each service should set receiver_phone, amount, product_code, etc. in __init__ or before calling.
        
        Returns:
            dict with responseCode, responseMessage, provider_ref, provider_avail_bal
        """
        pass

    @abc.abstractmethod
    def requery(self, transaction=None):
        """Requery the provider for the transaction status."""
        pass

    @abc.abstractmethod
    def get_balance(self):
        """Get the balance from the provider."""
        pass