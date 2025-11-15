from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.cache import cache

from apps.provider.models import Provider, ProviderAccount
from apps.product.models import ProductCategory, Product
from apps.merchant.models import User, Merchant


# Config schemas for each provider
PROVIDER_CONFIG_SCHEMAS = {
    "MTN": {
        "username": {"type": "string", "required": True, "description": "Username for MTN API"},
        "password": {"type": "string", "required": True, "description": "Password for MTN API"},
    },
    "AIRTEL": {
        "login_pin": {"type": "string", "required": True, "description": "Login PIN for Airtel API"},
    },
    "GLO": {
        "user_id": {"type": "string", "required": True, "description": "User ID for GLO API"},
        "password": {"type": "string", "required": True, "description": "Password for GLO API"},
        "reseller_id": {"type": "string", "required": True, "description": "Reseller ID for GLO API"},
        "client_id": {"type": "string", "required": True, "description": "Client ID for GLO API"},
    },
    "9MOBILE": {
        "username": {"type": "string", "required": True, "description": "Username for 9Mobile API"},
        "password": {"type": "string", "required": True, "description": "Password for 9Mobile API"},
        "auth_key": {"type": "string", "required": True, "description": "Authentication key for 9Mobile API"},
        "auth_token": {"type": "string", "required": True, "description": "Authentication token for 9Mobile API"},
    },
    "PAYANTAGE": {
        "password": {"type": "string", "required": True, "description": "Password for Payantage API"},
        "auth_token": {"type": "string", "required": True, "description": "Authentication token for Payantage API"},
    },
}

# Default config values for provider accounts (these should be updated with actual values)
PROVIDER_DEFAULT_CONFIGS = {
    "MTN": {
        "username": "",  # Set actual username
        "password": "",  # Set actual password
    },
    "AIRTEL": {
        "login_pin": "",  # Set actual PIN
    },
    "GLO": {
        "user_id": "",  # Set actual user ID
        "password": "",  # Set actual password
        "reseller_id": "",  # Set actual reseller ID
        "client_id": "",  # Set actual client ID
    },
    "9MOBILE": {
        "username": "",  # Set actual username
        "password": "",  # Set actual password
        "auth_key": "",  # Set actual auth key
        "auth_token": "",  # Set actual auth token
    },
    "PAYANTAGE": {
        "password": "",  # Set actual password
        "auth_token": "",  # Set actual token
    },
}

PROVIDERS = [
    {"name": "MTN Nigeria", "provider_code": "MTN", "description": "MTN Nigeria VAS provider", "is_active": True},
    {"name": "GLO Nigeria", "provider_code": "GLO", "description": "GLO Nigeria VAS provider", "is_active": True},
    {"name": "Airtel Nigeria", "provider_code": "AIRTEL", "description": "Airtel Nigeria VAS provider", "is_active": True},
    {"name": "9Mobile Nigeria", "provider_code": "9MOBILE", "description": "9Mobile Nigeria VAS provider", "is_active": True},
]

CATEGORIES = [
    {"name": "Airtime", "category_code": "AIRTIME", "description": "Mobile airtime top-up"},
    {"name": "Data", "category_code": "DATA", "description": "Mobile data bundles"},
]

PRODUCTS = [
    {
        "product_name": "MTN Airtime",
        "product_code": "MTNVTU",
        "description": "MTN airtime top-up",
        "category_code": "AIRTIME",
        "provider_code": "MTN",
        "provider_account_name": "MTN", # this is the account name in the provider
    },
    {
        "product_name": "GLO Airtime",
        "product_code": "GLOVTU",
        "description": "GLO airtime top-up",
        "category_code": "AIRTIME",
        "provider_code": "GLO",
        "provider_account_name": "GLO", # this is the account name in the provider
    },
    {
        "product_name": "Airtel Airtime",
        "product_code": "AIRTELVTU",
        "description": "Airtel airtime top-up",
        "category_code": "AIRTIME",
        "provider_code": "AIRTEL",
        "provider_account_name": "AIRTEL", # this is the account name in the provider
    },
    {
        "product_name": "9Mobile airtime",
        "product_code": "9MOBILEVTU",
        "description": "9Mobile airtime top-up",
        "category_code": "AIRTIME",
        "provider_code": "9MOBILE",
        "provider_account_name": "9MOBILE", # this is the account name in the provider
    },
    #= data products =#
    {
        "product_name": "MTN Data",
        "product_code": "MTNDATA",
        "description": "MTN data bundles",
        "category_code": "DATA",
        "provider_code": "MTN",
        "provider_account_name": "MTN", # this is the account name in the provider
    },
    {
        "product_name": "GLO Data",
        "product_code": "GLODATA",
        "description": "GLO data bundles",
        "category_code": "DATA",
        "provider_code": "GLO",
        "provider_account_name": "GLO", # this is the account name in the provider
    },  
    {
        "product_name": "Airtel Data",
        "product_code": "AIRTELDATA",
        "description": "Airtel data bundles",
        "category_code": "DATA",
        "provider_code": "AIRTEL",
        "provider_account_name": "AIRTEL", # this is the account name in the provider
    },
    {
        "product_name": "9Mobile Data",
        "product_code": "9MOBILEDATA",
        "description": "9Mobile data bundles",
        "category_code": "DATA",
        "provider_code": "9MOBILE",
        "provider_account_name": "9MOBILE", # this is the account name in the provider
    },
]


def seed_providers():
    """Seed providers and create default provider accounts"""
    provider_code_map = {}
    provider_account_map = {}
    
    for provider in PROVIDERS:
        provider_code = provider["provider_code"]
        
        # Get config schema for this provider
        config_schema = PROVIDER_CONFIG_SCHEMAS.get(provider_code, {})
        
        obj, _ = Provider.objects.get_or_create(
            provider_code=provider_code,
            defaults={
                "name": provider["name"],
                "description": provider.get("description", ""),
                "is_active": provider.get("is_active", True),
                "config_schema": config_schema,
            },
        )
        updated = False
        if obj.name != provider["name"]:
            obj.name = provider["name"]
            updated = True
        if obj.description != provider.get("description", ""):
            obj.description = provider.get("description", "")
            updated = True
        if obj.config_schema != config_schema:
            obj.config_schema = config_schema
            updated = True
        desired_status = provider.get("is_active", True)
        if obj.is_active != desired_status:
            obj.is_active = desired_status
            updated = True
        if updated:
            obj.save()
        provider_code_map[provider_code] = obj
        
        # Get default config for this provider account
        default_config = PROVIDER_DEFAULT_CONFIGS.get(provider_code, {}).copy()
        
        # Create default provider account for each provider
        # Use provider_code as account_name to match PRODUCTS configuration
        account_name = provider_code
        account, created = ProviderAccount.objects.get_or_create(
            provider=obj,
            account_name=account_name,
            defaults={
                "available_balance": 0.0,
                "balance_at_provider": 0.0,
                "config": default_config,
            }
        )
        
        # Update config if account already exists but config is empty or different
        if not created:
            if not account.config or account.config == {}:
                account.config = default_config
                account.save()
        
        provider_account_map[account_name] = account
    
    return provider_code_map, provider_account_map


def seed_categories():
    code_to_category = {}
    for cat in CATEGORIES:
        obj, _ = ProductCategory.objects.get_or_create(
            category_code=cat["category_code"],
            defaults={
                "name": cat["name"],
                "description": cat.get("description", ""),
                "is_active": True,
            },
        )
        updated = False
        if obj.name != cat["name"]:
            obj.name = cat["name"]
            updated = True
        if obj.description != cat.get("description", ""):
            obj.description = cat.get("description", "")
            updated = True
        if updated:
            obj.save()
        code_to_category[cat["category_code"]] = obj
    return code_to_category


def seed_products(provider_code_map, provider_account_map, category_code_map):
    """Seed products with provider accounts"""
    for prod in PRODUCTS:
        # Get category
        category = None
        category_id = prod.get("category_id")
        if category_id:
            category = ProductCategory.objects.filter(id=category_id).first()
            if not category:
                raise CommandError(
                    f"Category with id '{category_id}' referenced by product '{prod['product_code']}' does not exist."
                )
        else:
            category_code = prod.get("category_code")
            if not category_code:
                raise CommandError(
                    f"Product '{prod['product_code']}' must include either 'category_id' or 'category_code'."
                )
            if category_code not in category_code_map:
                raise CommandError(
                    f"Category '{category_code}' referenced by product '{prod['product_code']}' has not been seeded."
                )
            category = category_code_map[category_code]
        
        # Get provider account
        provider_account_name = prod.get("provider_account_name")
        provider_account = None
        if provider_account_name:
            if provider_account_name not in provider_account_map:
                # Try to find by provider code and account name
                provider_code = prod.get("provider_code")
                if provider_code and provider_code in provider_code_map:
                    provider = provider_code_map[provider_code]
                    provider_account = ProviderAccount.objects.filter(
                        provider=provider,
                        account_name=provider_account_name
                    ).first()
                    if provider_account:
                        provider_account_map[provider_account_name] = provider_account
                
                if not provider_account:
                    raise CommandError(
                        f"Provider account '{provider_account_name}' for product '{prod['product_code']}' not found. "
                        f"Please create it first or check the account name."
                    )
            else:
                provider_account = provider_account_map[provider_account_name]

        obj, _ = Product.objects.get_or_create(
            product_code=prod["product_code"],
            defaults={
                "product_name": prod["product_name"],
                "description": prod["description"],
                "is_active": True,
                "category": category,
                "preferred_provider_account": provider_account,
            },
        )

        updated = False
        if obj.product_name != prod["product_name"]:
            obj.product_name = prod["product_name"]
            updated = True
        if obj.description != prod["description"]:
            obj.description = prod["description"]
            updated = True
        if obj.category_id != category.id:
            obj.category = category
            updated = True
        if obj.preferred_provider_account != provider_account:
            obj.preferred_provider_account = provider_account
            updated = True
        if updated:
            obj.save()


def seed_users_and_merchant(stdout=None):
    """Seed super admin user, normal user, and merchant"""
    def write(msg):
        if stdout:
            stdout.write(msg + "\n")
        else:
            print(msg)
    
    # Create super admin user
    super_admin, created = User.objects.get_or_create(
        email="admin@telko.com",
        defaults={
            "username": "admin",
            "first_name": "Super",
            "last_name": "Admin",
            "is_superuser": True,
            "is_staff": True,
            "is_active": True,
            "email_verified": True,
        }
    )
    if created:
        super_admin.set_password("admin123")  # Default password, should be changed in production
        super_admin.save()
        write(f"Created super admin user: {super_admin.email} (password: admin123)")
    else:
        write(f"Super admin user already exists: {super_admin.email}")
    
    # Create normal user
    normal_user, created = User.objects.get_or_create(
        email="merchant@telko.com",
        defaults={
            "username": "merchant",
            "first_name": "Merchant",
            "last_name": "User",
            "is_superuser": False,
            "is_staff": False,
            "is_active": True,
            "email_verified": True,
        }
    )
    if created:
        normal_user.set_password("merchant123")  # Default password, should be changed in production
        normal_user.save()
        write(f"Created normal user: {normal_user.email} (password: merchant123)")
    else:
        write(f"Normal user already exists: {normal_user.email}")
    
    # Create merchant for the normal user
    merchant, created = Merchant.objects.get_or_create(
        user=normal_user,
        defaults={
            "business_name": "Telko Test Merchant",
            "business_description": "Test merchant account for development",
            "account_type": "Prepaid",
            "is_active": True,
            "current_balance": 100000.00,  # Initial balance for testing
        }
    )
    if created:
        write(f"Created merchant: {merchant.business_name} (Code: {merchant.merchant_code})")
    else:
        write(f"Merchant already exists: {merchant.business_name} (Code: {merchant.merchant_code})")
    
    return {
        "super_admin": super_admin,
        "normal_user": normal_user,
        "merchant": merchant
    }


class Command(BaseCommand):
    help = "Seed users, merchant, providers, product categories, and products"

    @transaction.atomic
    def handle(self, *args, **options):
        # Seed users and merchant
        seed_users_and_merchant(self.stdout)
        
        # Seed providers, categories, and products
        provider_map, provider_account_map = seed_providers()
        category_map = seed_categories()
        seed_products(provider_map, provider_account_map, category_map)
        
        # Clear product-related caches after seeding
        cache.delete("product_categories_active")
        # Clear product caches (pattern-based clearing would require django-redis)
        self.stdout.write(self.style.WARNING("Note: Product caches may need manual clearing if using Redis"))

        self.stdout.write(self.style.SUCCESS("Seeded users, merchant, providers, provider accounts, product categories, and products successfully."))


__all__ = [
    "PROVIDERS",
    "CATEGORIES",
    "PRODUCTS",
    "PROVIDER_CONFIG_SCHEMAS",
    "PROVIDER_DEFAULT_CONFIGS",
    "seed_providers",
    "seed_categories",
    "seed_products",
    "seed_users_and_merchant",
]

