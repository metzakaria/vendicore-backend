from django.db import models


# Create your models here.

#=============================================#
#********** Provider Model **************#
#=============================================#
class Provider(models.Model):
    name = models.CharField( max_length=200)
    provider_code = models.CharField( unique=True,max_length=50)
    description = models.TextField(null=True, blank=True)
    config_schema = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField( auto_now_add=True, null=True)
    updated_at = models.DateTimeField( auto_now=True, null=True)

    class Meta:
        db_table = 'vas_providers'
        indexes = [
            models.Index(fields=['provider_code','is_active']),
        ]

    def __str__(self):
        return f"{str(self.name)}"




#=============================================#
#********** Provider Account Model **************#
#=============================================#
class ProviderAccount(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    account_name = models.CharField(max_length=50)
    available_balance = models.FloatField(default = '0.0')
    balance_at_provider = models.FloatField(default='0.0')
    vending_sim = models.CharField( max_length=50, null=True, blank=True)
    config = models.JSONField(default=dict, null=True, blank=True)
    created_at = models.DateTimeField( auto_now_add=True, null=True)
    updated_at = models.DateTimeField( auto_now=True, null=True)

    class Meta:
        db_table = 'vas_provider_accounts'
        indexes = [
            models.Index(fields=['provider','account_name']),
        ]