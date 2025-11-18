#!/usr/bin/env python3
"""
Test script for CreditSwitch and Payvantage provider integrations
"""
import os
import sys
import django

# Add the project path
sys.path.append('/home/sherif_san/Documents/codes/vendicore-backend/api')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.provider.services import CreditswitchProviderService, PayvantageProviderService
from apps.provider.models import Provider, ProviderAccount

class MockProviderAccount:
    """Mock provider account for testing"""
    def __init__(self, config):
        self.config = config
        self.vending_sim = ""

def test_creditswitch():
    """Test CreditSwitch integration"""
    print("=" * 50)
    print("TESTING CREDITSWITCH")
    print("=" * 50)
    
    # Configure your CreditSwitch credentials here
    config = {
        'login_id': 'YOUR_LOGIN_ID',
        'public_key': 'YOUR_PUBLIC_KEY', 
        'private_key': 'YOUR_PRIVATE_KEY',
        'base_url': 'https://api.creditswitch.com',  # Replace with actual base URL
        'timeout': 30,
        'verify_ssl': True
    }
    
    provider_account = MockProviderAccount(config)
    
    # Test 1: Airtime vending
    print("\n1. Testing Airtime Vending (₦100 to MTN)")
    service = CreditswitchProviderService(
        provider_account=provider_account,
        receiver_phone="08012345678",  # Replace with test number
        amount=10000,  # ₦100 in kobo
        product_code="MTNVTU"
    )
    
    try:
        response = service.send_request()
        print(f"Response Code: {response['responseCode']}")
        print(f"Message: {response['responseMessage']}")
        print(f"Provider Ref: {response['provider_ref']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Data vending
    print("\n2. Testing Data Vending (MTN 1GB)")
    service = CreditswitchProviderService(
        provider_account=provider_account,
        receiver_phone="08012345678",  # Replace with test number
        amount=100000,  # ₁000 in kobo
        product_code="MTNDATA",
        product_id="MTN-1GB-30"  # Replace with actual product ID
    )
    
    try:
        response = service.send_request()
        print(f"Response Code: {response['responseCode']}")
        print(f"Message: {response['responseMessage']}")
        print(f"Provider Ref: {response['provider_ref']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Get data plans
    print("\n3. Testing Get Data Plans (MTN)")
    try:
        plans = service.get_data_plans("D04D")  # MTN data service ID
        print(f"Plans response: {plans}")
    except Exception as e:
        print(f"Error: {e}")

def test_payvantage():
    """Test Payvantage integration"""
    print("\n" + "=" * 50)
    print("TESTING PAYVANTAGE")
    print("=" * 50)
    
    # Configure your Payvantage credentials here
    config = {
        'api_key': 'YOUR_API_KEY',
        'client_id': 'YOUR_CLIENT_ID',
        'base_url': 'https://api.payvantage.com',  # Replace with actual base URL
        'timeout': 30,
        'verify_ssl': True
    }
    
    provider_account = MockProviderAccount(config)
    
    # Test 1: Airtime vending
    print("\n1. Testing Airtime Vending (₦100 to MTN)")
    service = PayvantageProviderService(
        provider_account=provider_account,
        receiver_phone="08012345678",  # Replace with test number
        amount=10000,  # ₦100 in kobo
        product_code="MTNVTU"
    )
    
    try:
        response = service.send_request()
        print(f"Response Code: {response['responseCode']}")
        print(f"Message: {response['responseMessage']}")
        print(f"Provider Ref: {response['provider_ref']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Data vending
    print("\n2. Testing Data Vending (MTN 2GB)")
    service = PayvantageProviderService(
        provider_account=provider_account,
        receiver_phone="08012345678",  # Replace with test number
        amount=120000,  # ₦1200 in kobo
        product_code="MTNDATA",
        plan_code="1005"  # 2GB Monthly Plan
    )
    
    try:
        response = service.send_request()
        print(f"Response Code: {response['responseCode']}")
        print(f"Message: {response['responseMessage']}")
        print(f"Provider Ref: {response['provider_ref']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Get data packages
    print("\n3. Testing Get Data Packages (MTN)")
    try:
        packages = service.get_data_packages("MTN")
        if packages['success']:
            print(f"Found {len(packages['packages'])} packages")
            # Show first 3 packages
            for i, package in enumerate(packages['packages'][:3]):
                print(f"  {i+1}. {package['bundle_value']} - ₦{package['bundle_price']} - Code: {package['plan_code']}")
        else:
            print(f"Error: {packages['message']}")
    except Exception as e:
        print(f"Error: {e}")

def test_manager_integration():
    """Test manager integration"""
    print("\n" + "=" * 50)
    print("TESTING MANAGER INTEGRATION")
    print("=" * 50)
    
    from apps.provider.manager import ProviderServiceManager
    
    # You would need actual ProviderAccount objects from database
    print("Note: Manager integration requires actual ProviderAccount objects from database")
    print("Example usage:")
    print("""
    # Get your provider account from database
    creditswitch_account = ProviderAccount.objects.get(provider__provider_code='CREDITSWITCH')
    payvantage_account = ProviderAccount.objects.get(provider__provider_code='PAYVANTAGE')
    
    # Test via manager
    response = ProviderServiceManager.vend(
        provider_account=creditswitch_account,
        receiver_phone="08012345678",
        amount=10000,
        product_code="MTNVTU",
        data_code="",
        tariff_type_id="1"
    )
    """)

if __name__ == "__main__":
    print("Provider Integration Test Script")
    print("IMPORTANT: Update the credentials in this script before running!")
    print("\nWhat to update:")
    print("1. Replace YOUR_LOGIN_ID, YOUR_PUBLIC_KEY, YOUR_PRIVATE_KEY for CreditSwitch")
    print("2. Replace YOUR_API_KEY, YOUR_CLIENT_ID for Payvantage")
    print("3. Replace base URLs with actual API endpoints")
    print("4. Replace test phone numbers with actual test numbers")
    print("5. Update product IDs and plan codes as needed")
    
    choice = input("\nEnter 'c' for CreditSwitch, 'p' for Payvantage, 'm' for manager, or 'a' for all: ").lower()
    
    if choice in ['c', 'a']:
        test_creditswitch()
    
    if choice in ['p', 'a']:
        test_payvantage()
    
    if choice in ['m', 'a']:
        test_manager_integration()
    
    print("\nTest completed!")
