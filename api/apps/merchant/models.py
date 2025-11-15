import random
import uuid
import datetime
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.product.models import Product
# Create your models here.
#User
#=============================================#
#********** Merchant Model **************#
#=============================================#
class Merchant(models.Model):
    ACCOUNT_TYPE = [
        ("Prepaid", "Prepaid"),
        ("Postpaid", "Postpaid"),
    ]
    merchant_code = models.CharField(max_length=10, unique=True,blank=True)
    business_name = models.CharField(max_length=200)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100,blank=True, null=True)
    state = models.CharField(max_length=100,blank=True, null=True)
    country = models.CharField(max_length=100,blank=True, null=True)
    website = models.CharField(max_length=100,blank=True, null=True)
    balance_before = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    business_description = models.TextField(blank=True, null=True)
    api_access_ip = models.CharField(max_length=30,blank=True, null=True)
    account_type = models.CharField(max_length=10,choices=ACCOUNT_TYPE, default="Prepaid")
    daily_tranx_limit = models.CharField(max_length=200,blank=True, null=True, default="0")
    today_tranx_value = models.CharField(max_length=200,blank=True, null=True, default="0")
    today_tranx_date = models.DateField(max_length=30,blank=True, null=True)
    api_secret_key = models.TextField(blank=True, null=True)
    api_token = models.TextField(blank=True, null=True)
    api_token_created = models.DateTimeField( null=True)
    api_token_expire = models.DateTimeField( null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField( null=True)
    last_updated_balance_at = models.DateTimeField( null=True)
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='merchant_profile', related_query_name='merchant_profile', null=True,blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # Only generate value on the first create
            self.merchant_code = self._generate_unique_value()
        super().save(*args, **kwargs)
    
    def _generate_unique_value(self):
        # Generate random 7-digit numeric value
        value = random.randint(1000000, 9999999)
        # Ensure the generated value is unique
        while Merchant.objects.filter(merchant_code=value).exists():
            value = random.randint(1000000, 9999999)
        return str(value)
    
    #debit balance
    @transaction.atomic()
    def debit_balance(self, amount: Decimal):
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        merchant = Merchant.objects.select_for_update().get(id=self.id)
        if merchant.current_balance < amount:
            raise ValueError(f"Insufficient balance, your balance is NGN{merchant.current_balance}")
        merchant.balance_before = merchant.current_balance
        merchant.current_balance = F('current_balance') - amount
        merchant.last_updated_balance_at = timezone.now()
        merchant.save(update_fields=['current_balance','balance_before','last_updated_balance_at'])
        merchant.refresh_from_db()
        return merchant
    
    #credit balance
    @transaction.atomic()
    def credit_balance(self, amount: Decimal, source: str="auto_reversal"):
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        
        merchant = Merchant.objects.select_for_update().get(id=self.id)
        merchant.balance_before = merchant.current_balance
        merchant.current_balance = F('current_balance') + amount
        merchant.last_updated_balance_at = timezone.now()
        merchant.save(update_fields=['current_balance','balance_before','last_updated_balance_at'])
        merchant.refresh_from_db()
        MerchantFunding.objects.create(
            amount=amount,
            description="Credit balance",
            merchant=merchant,
            source=source,
            is_approved=True,
            is_active=True,
            approvedby=merchant.user,
            approved_at=timezone.now(),
            is_credited=True,
            createdby=merchant.user,
            balance_before=merchant.balance_before,
            balance_after=merchant.current_balance
        )
        return merchant


    class Meta:
        db_table = "vas_merchants"
        indexes = [
            models.Index(fields=['merchant_code'], name='merchant_code_index'),
            #models.Index(fields=["last_name", "first_name"]),
        ]




#=============================================#
#********** User Model **************#
#=============================================#
class User(AbstractUser):
    email = models.EmailField(max_length=254, unique=True)
    phone_number = models.CharField(max_length=15, null=True,blank=True)
    email_verified = models.BooleanField(default=False)
    email_verified_at =  models.DateField(max_length=30,blank=True, null=True)
    email_verify_token = models.CharField(max_length=250,blank=True, null=True)

    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name','username']

    def __str__(self):
        return self.email

    class Meta:
      db_table = "vas_users"



#=============================================#
#********** Merchant Discount Model **************#
#=============================================#
class MerchantDiscount(models.Model):
    DISCOUNT_TYPE = [
        ("percentage", "Percentage"),
        ("fixed", "Fixed"),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='merchant_discounts')
    discount_type = models.CharField(max_length=100, choices=DISCOUNT_TYPE)
    discount_value = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='merchant_discounts')
    createdby = models.ForeignKey(User, on_delete=models.CASCADE,  db_column='created_by', related_name='createdby_merchant_discount',null=True)
    updatedby = models.ForeignKey(User, on_delete=models.CASCADE,  db_column='updated_by', related_name='updatedby_merchant_discount',null=True)

    class Meta:
        db_table = "vas_merchant_discount"
        indexes = [
            models.Index(fields=['discount_type','is_active']),
        ]
        

#=============================================#
#********** Merchant Funding Model **************#
#=============================================#
class MerchantFunding(models.Model):
    FUNDING_SOURCE = [
        ("admin", "Admin"),
        ("auto_reversal", "Auto Reversal"),
        ("manual_reversal", "Manual Reversal"),
    ]   
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField()
    funding_ref = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField( null=True, auto_now_add=True)
    createdby = models.ForeignKey(User, on_delete=models.CASCADE,db_column='created_by',related_name='merchantfunding_createdby')
    is_approved = models.BooleanField(default=False)
    balance_before = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    source = models.CharField(max_length=100, choices=FUNDING_SOURCE)
    is_active = models.BooleanField(default=True)
    approvedby = models.ForeignKey(User, on_delete=models.CASCADE,db_column='approved_by',related_name='merchant_funding_approvedby',null=True,blank=True)
    approved_at = models.DateTimeField( null=True,blank=True)
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE,related_name='merchant_funding')
    is_credited = models.BooleanField(default=False)

    class Meta:
       db_table = "vas_merchant_funding"
       indexes = [
           models.Index(fields=["funding_ref","is_approved","is_active"])
       ]
       verbose_name = 'MerchantFunding'
       verbose_name_plural = 'MerchantFundings'

