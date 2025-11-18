from django.core.management.base import BaseCommand
from apps.provider.services import CreditswitchProviderService, PayvantageProviderService

class MockProviderAccount:
    def __init__(self, config):
        self.config = config
        self.vending_sim = ""

class Command(BaseCommand):
    help = 'Test CreditSwitch and Payvantage provider integrations'

    def add_arguments(self, parser):
        parser.add_argument('--provider', choices=['creditswitch', 'payvantage'], required=True)
        parser.add_argument('--phone', required=True, help='Test phone number')
        parser.add_argument('--amount', type=int, default=10000, help='Amount in kobo (default: 10000 = ₦100)')
        parser.add_argument('--product', default='MTNVTU', help='Product code (default: MTNVTU)')
        parser.add_argument('--plan-code', help='Plan code for data (Payvantage only)')
        parser.add_argument('--product-id', help='Product ID for data (CreditSwitch only)')

    def handle(self, *args, **options):
        if options['provider'] == 'creditswitch':
            self.test_creditswitch(options)
        elif options['provider'] == 'payvantage':
            self.test_payvantage(options)

    def test_creditswitch(self, options):
        self.stdout.write("Testing CreditSwitch...")
        
        config = {
            'login_id': 'YOUR_LOGIN_ID',
            'public_key': 'YOUR_PUBLIC_KEY',
            'private_key': 'YOUR_PRIVATE_KEY',
            'base_url': 'https://api.creditswitch.com',
            'timeout': 30,
            'verify_ssl': True
        }
        
        provider_account = MockProviderAccount(config)
        
        service = CreditswitchProviderService(
            provider_account=provider_account,
            receiver_phone=options['phone'],
            amount=options['amount'],
            product_code=options['product'],
            product_id=options.get('product_id', '')
        )
        
        try:
            response = service.send_request()
            self.stdout.write(f"Response Code: {response['responseCode']}")
            self.stdout.write(f"Message: {response['responseMessage']}")
            self.stdout.write(f"Provider Ref: {response['provider_ref']}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))

    def test_payvantage(self, options):
        self.stdout.write("Testing Payvantage...")
        
        config = {
            'api_key': 'YOUR_API_KEY',
            'client_id': 'YOUR_CLIENT_ID',
            'base_url': 'https://api.payvantage.com',
            'timeout': 30,
            'verify_ssl': True
        }
        
        provider_account = MockProviderAccount(config)
        
        service = PayvantageProviderService(
            provider_account=provider_account,
            receiver_phone=options['phone'],
            amount=options['amount'],
            product_code=options['product'],
            plan_code=options.get('plan_code', '1005')
        )
        
        try:
            response = service.send_request()
            self.stdout.write(f"Response Code: {response['responseCode']}")
            self.stdout.write(f"Message: {response['responseMessage']}")
            self.stdout.write(f"Provider Ref: {response['provider_ref']}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
