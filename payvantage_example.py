"""
Example usage of Payvantage Provider Service

This file demonstrates how to use the Payvantage service for data vending
and retrieving data packages.
"""

from apps.provider.services import PayvantageProviderService
from apps.provider.models import ProviderAccount, Provider

def example_data_vending():
    """Example of how to vend data using Payvantage."""
    
    # Assuming you have a ProviderAccount configured in your database
    # with the following config:
    config = {
        'api_key': 'your-api-key-here',
        'client_id': 'your-client-id-here',
        'base_url': 'https://api.payvantage.com',  # Replace with actual base URL
        'timeout': 30,
        'verify_ssl': True
    }
    
    # Create or get your provider account
    # provider_account = ProviderAccount.objects.get(provider__provider_code='PAYVANTAGE')
    
    # Example vending request
    service = PayvantageProviderService(
        provider_account=None,  # Replace with actual provider_account
        receiver_phone="08169643167",
        amount=1200,  # Amount in kobo/cents
        product_code="MTNDATA",
        plan_code="1005"  # 2GB Monthly Plan from the documentation
    )
    
    # Send the vending request
    response = service.send_request()
    
    print("Vending Response:")
    print(f"Response Code: {response['responseCode']}")
    print(f"Message: {response['responseMessage']}")
    print(f"Provider Reference: {response['provider_ref']}")
    
    return response

def example_get_packages():
    """Example of how to get data packages for a network."""
    
    config = {
        'api_key': 'your-api-key-here',
        'client_id': 'your-client-id-here',
        'base_url': 'https://api.payvantage.com',
        'timeout': 30,
        'verify_ssl': True
    }
    
    service = PayvantageProviderService(
        provider_account=None,  # Replace with actual provider_account
    )
    
    # Get MTN data packages
    packages = service.get_data_packages("MTN")
    
    if packages['success']:
        print("Available MTN Data Packages:")
        for package in packages['packages']:
            print(f"Plan Code: {package['plan_code']}")
            print(f"Bundle: {package['bundle_value']}")
            print(f"Price: ₦{package['bundle_price']}")
            print(f"Validity: {package['bundle_validity']}")
            print("---")
    else:
        print(f"Error getting packages: {packages['message']}")
    
    return packages

def integration_with_manager():
    """Example of how the manager integrates with Payvantage."""
    
    from apps.provider.manager import ProviderServiceManager
    
    # Example usage through the manager
    # This assumes you have a ProviderAccount with provider_code='PAYVANTAGE'
    
    response = ProviderServiceManager.vend(
        provider_account=None,  # Your PAYVANTAGE provider account
        receiver_phone="08169643167",
        amount=1200,
        product_code="MTNDATA",
        data_code="1005",  # This becomes plan_code in Payvantage
        tariff_type_id="1"
    )
    
    return response

if __name__ == "__main__":
    print("Payvantage Integration Examples")
    print("=" * 40)
    
    # Note: These examples won't run without proper database setup
    # and valid API credentials
    
    print("\n1. Data Vending Example:")
    print("service = PayvantageProviderService(...)")
    print("response = service.send_request()")
    
    print("\n2. Get Packages Example:")
    print("packages = service.get_data_packages('MTN')")
    
    print("\n3. Manager Integration:")
    print("response = ProviderServiceManager.vend(...)")
    
    print("\nConfiguration required in ProviderAccount.config:")
    print({
        'api_key': 'your-payvantage-api-key',
        'client_id': 'your-payvantage-client-id',
        'base_url': 'https://api.payvantage.com',
        'timeout': 30,
        'verify_ssl': True
    })
