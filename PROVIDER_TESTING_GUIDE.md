# Provider Testing Guide

## Quick Setup

### 1. Update Credentials

Edit the test files and replace placeholder credentials:

**For CreditSwitch:**
- `YOUR_LOGIN_ID` - Your merchant login ID
- `YOUR_PUBLIC_KEY` - Your public key
- `YOUR_PRIVATE_KEY` - Your private key
- Base URL (if different from default)

**For Payvantage:**
- `YOUR_API_KEY` - Your API key
- `YOUR_CLIENT_ID` - Your client ID  
- Base URL (if different from default)

### 2. Testing Options

#### Option 1: Standalone Script
```bash
cd /home/sherif_san/Documents/codes/vendicore-backend
python test_providers.py
```

#### Option 2: Django Management Command
```bash
cd /home/sherif_san/Documents/codes/vendicore-backend/api

# Test CreditSwitch airtime
python manage.py test_providers --provider creditswitch --phone 08012345678 --amount 10000 --product MTNVTU

# Test CreditSwitch data
python manage.py test_providers --provider creditswitch --phone 08012345678 --amount 100000 --product MTNDATA --product-id "MTN-1GB-30"

# Test Payvantage airtime
python manage.py test_providers --provider payvantage --phone 08012345678 --amount 10000 --product MTNVTU

# Test Payvantage data
python manage.py test_providers --provider payvantage --phone 08012345678 --amount 120000 --product MTNDATA --plan-code 1005
```

### 3. Database Integration Testing

Once you have Provider and ProviderAccount records in your database:

```python
from apps.provider.manager import ProviderServiceManager
from apps.provider.models import ProviderAccount

# Get your provider accounts
creditswitch_account = ProviderAccount.objects.get(provider__provider_code='CREDITSWITCH')
payvantage_account = ProviderAccount.objects.get(provider__provider_code='PAYVANTAGE')

# Test airtime via manager
response = ProviderServiceManager.vend(
    provider_account=creditswitch_account,
    receiver_phone="08012345678",
    amount=10000,  # ₦100 in kobo
    product_code="MTNVTU",
    data_code="",
    tariff_type_id="1"
)

# Test data via manager
response = ProviderServiceManager.vend(
    provider_account=payvantage_account,
    receiver_phone="08012345678", 
    amount=120000,  # ₦1200 in kobo
    product_code="MTNDATA",
    data_code="1005",  # Plan code
    tariff_type_id="1"
)
```

### 4. Expected Response Codes

- `00` - Success
- `01` - Failed
- `02` - Pending
- `07` - Duplicate
- `08` - Invalid request
- `80` - Timeout
- `90` - System error

### 5. Troubleshooting

1. **Check credentials** - Ensure all API keys are correct
2. **Check base URLs** - Verify endpoints are correct
3. **Check phone numbers** - Use valid test numbers
4. **Check amounts** - Ensure amounts are in kobo (multiply naira by 100)
5. **Check logs** - Look at Django logs for detailed error messages
6. **Check network** - Ensure server can reach provider APIs

### 6. Production Setup

Create ProviderAccount records in your database:

```python
# Example for CreditSwitch
Provider.objects.create(
    name="CreditSwitch",
    provider_code="CREDITSWITCH",
    is_active=True
)

ProviderAccount.objects.create(
    provider=provider,
    account_name="CreditSwitch Main",
    is_active=True,
    config={
        'login_id': 'your_actual_login_id',
        'public_key': 'your_actual_public_key',
        'private_key': 'your_actual_private_key',
        'base_url': 'https://api.creditswitch.com',
        'timeout': 30,
        'verify_ssl': True
    }
)
```
