import abc
import logging
import random
import base64
import datetime

logger = logging.getLogger(__name__)

class BaseProvider(abc.ABC):
    def __init__(self, provider_account):
        """
        provider_account: ProviderAccount instance from DB
        provider_account.config: contains credentials, endpoints, etc.
        """
        self.account = provider_account
        self.config = provider_account.config or {}
        # Common config access with fallback to account fields
        self.url = self.config.get('url', '')
        self.vend_sim = self.config.get('vend_sim') or provider_account.vending_sim or ''
        self.timeout = self.config.get('timeout', 5)
        self.verify_ssl = self.config.get('verify_ssl', False)

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
    def requery(self, transaction):
        """Requery the provider for the transaction status."""
        pass