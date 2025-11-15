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
    PayantageProviderService,
)

logger = logging.getLogger(__name__)


class ProviderServiceManager:
    """
    Simple manager for provider service calls.
    Matches the pattern used in product views.
    """
    
    @classmethod
    def vend(cls, provider_account, receiver_phone, amount, product_code, data_code="", tariff_type_id="1"):
        """
        Vend airtime or data using the appropriate provider service.
        
        Args:
            provider_account: ProviderAccount instance from DB
            receiver_phone: Phone number to send to
            amount: Amount for airtime or data
            product_code: Product code (e.g., 'MTNVTU', 'MTNDATA', 'GLOVTU', etc.)
            data_code: Data bundle code (for data products)
            tariff_type_id: Tariff type ID (for MTN products, default '1')
        
        Returns:
            dict with responseCode, responseMessage, provider_ref, provider_avail_bal
        """
        try:
            provider_code = provider_account.provider.provider_code
            
            # MTN products
            if product_code in ["MTNVTU", "MTNDATA"]:
                if provider_code == "MTN":
                    service = MTNNProviderService(provider_account, receiver_phone, amount, tariff_type_id)
                    return service.send_request()
                elif provider_code == "PAYANTAGE":
                    service = PayantageProviderService(provider_account, receiver_phone, amount, tariff_type_id)
                    return service.send_request()
            
            # GLO products
            elif product_code in ["GLOVTU", "GLODATA"]:
                if provider_code == "GLO":
                    service = GloProviderService(provider_account, receiver_phone, amount, data_code, product_code)
                    return service.send_request()
                elif provider_code == "PAYANTAGE":
                    service = PayantageProviderService(provider_account, receiver_phone, amount, tariff_type_id)
                    return service.send_request()
            
            # Airtel products
            elif product_code in ["AIRTELVTU", "AIRTELDATA"]:
                if provider_code == "AIRTEL":
                    service = AirtelProviderService(provider_account, receiver_phone, amount, product_code)
                    return service.send_request()
                elif provider_code == "PAYANTAGE":
                    service = PayantageProviderService(provider_account, receiver_phone, amount, tariff_type_id)
                    return service.send_request()
            
            # 9Mobile products
            elif product_code in ["9MOBILEVTU", "9MOBILEDATA"]:
                if provider_code == "9MOBILE":
                    service = EtisalatProviderService(provider_account, receiver_phone, amount, product_code)
                    return service.send_request()
                elif provider_code == "PAYANTAGE":
                    service = PayantageProviderService(provider_account, receiver_phone, amount, tariff_type_id)
                    return service.send_request()
            
            # SME Data products
            elif product_code in ["MTNSMEDATA", "AIRTELSMEDATA", "GLOSMEDATA", "9MOBILESMEDATA"]:
                if provider_code == "PAYANTAGE":
                    service = PayantageProviderService(provider_account, receiver_phone, amount, product_code tariff_type_id)
                    return service.send_request()
            
            # No match found
            logger.warning(f"No provider service found for provider_code={provider_code}, product_code={product_code}")
            return {"responseCode": "99", "responseMessage": "Product code doesn't match", "provider_ref": None, "provider_avail_bal": "0"}
            
        except Exception as e:
            logger.error(f"Error vending via {provider_account.provider.provider_code}: {e}", exc_info=True)
            return {
                "responseCode": "90",
                "responseMessage": str(e),
                "provider_ref": "",
                "provider_avail_bal": "0"
            }

