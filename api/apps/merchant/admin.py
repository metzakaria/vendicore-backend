from django.contrib import admin

# Register your models here.
from .models import User,Merchant,MerchantDiscount,MerchantFunding

admin.site.register(User)
admin.site.register(Merchant)
admin.site.register(MerchantDiscount)
admin.site.register(MerchantFunding)