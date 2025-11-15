from django.contrib import admin

from .models import ProductCategory, Product,Transaction,DataPackage
# Register your models here.

admin.site.register(ProductCategory)
admin.site.register(Product)
admin.site.register(Transaction)
admin.site.register(DataPackage)