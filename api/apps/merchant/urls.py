from django.urls import path
from .views import MerchantApiView

urlpatterns = [
    path('generateMerchantJwtToken', MerchantApiView.as_view({'post': 'generate_merchant_jwt_token'}), name='generateMerchantJwtToken'),
]