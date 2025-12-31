from django.db import models
import uuid

from apps.provider.models import ProviderAccount, Provider

# Create your models here.

#=============================================#
#********** Product Category Model **************#
#=============================================#
class ProductCategory(models.Model):
    name = models.CharField( max_length=100)
    category_code = models.CharField(unique=True, max_length=100)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField( auto_now_add=True, null=True)
    updated_at = models.DateTimeField( auto_now=True,  null=True)

    class Meta:
        db_table = "vas_product_categories"
        indexes = [
            models.Index(fields=['category_code','is_active']),
        ]

    def __str__(self):
        return str(self.name)


#=============================================#
#********** Product Model **************#
#=============================================#
class Product(models.Model):
    product_name = models.CharField( max_length=200)
    product_code = models.CharField( unique=True, max_length=50)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField( auto_now_add=True, null=True)
    updated_at = models.DateTimeField( auto_now=True, null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    preferred_provider_account = models.ForeignKey(ProviderAccount, on_delete=models.CASCADE, related_name='preferred_provider_account',null=True,blank=True)
    backup_provider_account = models.ForeignKey(ProviderAccount, on_delete=models.CASCADE, related_name='backup_provider_account',null=True,blank=True)

    class Meta:
        db_table = "vas_products"
        indexes = [
            models.Index(fields=['product_code','preferred_provider_account','backup_provider_account','is_active']),
        ]

    @property
    def preferred_provider_code(self):
        """Get provider code from preferred_provider_account"""
        if self.preferred_provider_account and self.preferred_provider_account.provider:
            return self.preferred_provider_account.provider.provider_code
        return None
    
    def __str__(self):
        return f"{str(self.product_name)}"

#=============================================#
#********** Data Package Model **************#
#=============================================#
class DataPackage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='data_packages')
    data_code = models.CharField( max_length=100,unique=True)
    tariff_id = models.CharField( max_length=100,null=True)
    network = models.CharField( max_length=100,null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(null=True)
    short_desc = models.TextField(null=True)
    duration = models.CharField( max_length=200,null=True)
    value = models.CharField(max_length=200,null=True)
    plan_name = models.CharField(max_length=200,null=True)
    creditswitch_code = models.CharField( max_length=200,null=True)
    payvantage_code = models.CharField( max_length=200,null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField( null=True, auto_now_add=True)
    updated_at = models.DateTimeField( auto_now=True, null=True)

    class Meta:
        db_table = "vas_data_packages"
        indexes =[
            models.Index(fields=['product','is_active','data_code']),
        ]

    def __str__(self):
        return str(self.data_code)




#=============================================#
#********** Data Package Provider Model *******#
#=============================================#
class DataPackageProvider(models.Model):
    datapackage = models.ForeignKey(DataPackage, on_delete=models.CASCADE, related_name='data_packages_provider')
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='data_provider')
    provider_code = models.CharField( max_length=100)
    #cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField( null=True, auto_now_add=True)
    updated_at = models.DateTimeField( auto_now=True, null=True)

    class Meta:
        db_table = "vas_data_package_providers"
        unique_together = ("datapackage", "provider")
        indexes =[
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return str(self.provider_code)


#=============================================#
#********** Transaction Model **************#
#=============================================#
class Transaction(models.Model):
    _STATUS = [
        ("Processing", "Processing"),
        ("Pending", "Pending"),
        ("Success", "Success"),
        ("Failed", "Failed"),
    ]
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_before = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    beneficiary_account = models.CharField( max_length=50, unique_for_date="created_at")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transactions')
    product_category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='product_category_transactions')
    description = models.TextField()
    status = models.CharField( max_length=50, choices=_STATUS, default='Processing')
    is_reverse = models.BooleanField(default=False)
    reversed_at = models.DateTimeField( null=True, blank=True)
    provider_ref = models.CharField( max_length=230,null=True, blank=True)
    provider_desc = models.CharField( max_length=230,null=True, blank=True)
    merchant_ref = models.CharField( max_length=230,  unique=True)
    created_at = models.DateTimeField( auto_now_add=True,null=True)
    updated_at = models.DateTimeField( auto_now=True, null=True)
    merchant = models.ForeignKey('merchant.Merchant', on_delete=models.DO_NOTHING, related_name='transactions')
    provider_account = models.ForeignKey(ProviderAccount, on_delete=models.DO_NOTHING, null=True, blank=True)
   

    class Meta:
        db_table = 'vas_transactions'
        indexes = [
            models.Index(fields=['beneficiary_account','status','product','provider_ref','merchant_ref','created_at','product_category','amount']),
        ]

  
