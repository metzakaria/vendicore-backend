from rest_framework import serializers
from .models import DataPackage , Transaction, ProductCategory, Product
from apps.provider.models import Provider

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'category_code', 'description', 'is_active']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'product_name', 'product_code', 'description', 'is_active']

class DataPackageSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.product_code', read_only=True)
    
    class Meta:
        model = DataPackage
        fields = ['product_code', 'data_code', 'amount', 'description','duration','value']


class TransactionSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.product_code', read_only=True)
    
    class Meta:
        model = Transaction
        fields = ['amount','description', 'beneficiary_account', 'product_code','merchant_ref','created_at']


class ValidateVendDataSerializer(serializers.Serializer):
    product_code = serializers.CharField(max_length=100)
    data_code = serializers.CharField(max_length=100)
    phone_number = serializers.CharField(max_length=15)
    merchant_ref = serializers.CharField(max_length=250)

class ValidateVendVtuSerializer(serializers.Serializer):
    product_code = serializers.CharField(max_length=100)
    amount = serializers.IntegerField()
    phone_number = serializers.CharField(max_length=15)
    merchant_ref = serializers.CharField(max_length=250)
