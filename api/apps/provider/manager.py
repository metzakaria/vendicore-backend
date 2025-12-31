"""
Provider Service Manager

Simple manager that maps provider codes and product codes to their respective services.
"""
import logging

from apps.provider.services import (
    MTNNProviderService,
    AirtelProviderService,
    GloProviderService,
    EtisalatProviderService,
    PayvantageProviderService,
    CreditswitchProviderService,
)

logger = logging.getLogger(__name__)


class ProviderServiceManager:
    """
    Simple manager for provider service calls.
    Matches the pattern used in product views.
    """
    
    @classmethod
    def _get_provider_service(cls, provider_code):
        if provider_code == "PAYVANTAGE":
            return PayvantageProviderService
        elif provider_code == "MTN":
            return MTNNProviderService
        elif provider_code == "GLO":
            return GloProviderService
        elif provider_code == "AIRTEL":
            return AirtelProviderService
        elif provider_code == "9MOBILE":
            return EtisalatProviderService
        elif provider_code == "CREDITSWITCH":
            return CreditswitchProviderService
        else:
            return None

    @classmethod
    def vend(cls, provider_account, merchant_ref=None, receiver_phone=None, amount=None, product_code=None, data_code=None):
        """Vend airtime or data using the appropriate provider service."""
        try:
            provider_code = provider_account.provider.provider_code
            
            service = cls._get_provider_service(provider_code)
            if not service:
                logger.warning(f"No provider service found for provider_code={provider_code}")
                return {"responseCode": "99", "responseMessage": "Provider code doesn't match", "provider_ref": None, "provider_avail_bal": "0"}
            
            service = service(provider_account, merchant_ref=merchant_ref, receiver_phone=receiver_phone, amount=amount, product_code=product_code, data_code=data_code)
            return service.send_request()
            
        except Exception as e:
            logger.error(f"Error vending via {provider_account.provider.provider_code}: {e}", exc_info=True)
            return {
                "responseCode": "90",
                "responseMessage": str(e),
                "provider_ref": "",
                "provider_avail_bal": "0"
            }


    @classmethod
    def requery(cls, provider_account, merchant_ref=None, product_code=None):
        """Requery the provider service for the transaction status."""
        try:
            provider_code = provider_account.provider.provider_code
            service = cls._get_provider_service(provider_code)
            if not service:
                logger.warning(f"No provider service found for provider_code={provider_code}")
                return {"responseCode": "99", "responseMessage": "Provider code doesn't match", "provider_ref": None, "provider_avail_bal": "0"}
            service = service(provider_account, merchant_ref=merchant_ref, product_code=product_code)
            return service.requery()
        except Exception as e:
            logger.error(f"Error requerying via {provider_account.provider.provider_code}: {e}", exc_info=True)
            return {
                "responseCode": "90",
                "responseMessage": str(e),
                "provider_ref": "",
                "provider_avail_bal": "0"
            }