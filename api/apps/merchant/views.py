

from apps.merchant.models import Merchant
from config.helper import generate_merchant_jwt_token
from rest_framework import viewsets
from rest_framework.response import Response
from config.helper import JsonResponse
from rest_framework.permissions import AllowAny
import logging
logger = logging.getLogger(__name__)

class MerchantApiView(viewsets.ViewSet):
    authentication_classes = []
    #permission_classes = [AllowAny]
    
    def generate_merchant_jwt_token(self, request):
        try:
            merchant_code = request.data.get('merchant_code')
            logger.info(f"GENERATE MERCHANT JWT TOKEN:: MERCHANT CODE ={merchant_code}")
            merchant = Merchant.objects.filter(merchant_code=merchant_code, is_active=True).first() 
            logger.info(f"MERCHANT::{merchant}")
            if not merchant:
                return JsonResponse(code="01", msg = "Merchant not found or inactive")
            api_secret_key = merchant.api_secret_key
            if not api_secret_key:
                return JsonResponse(code="01", msg = "API Secret Key not properly configured")
            expiration_minutes = request.data.get('expiration_minutes', 60)
            token = generate_merchant_jwt_token(merchant_code, api_secret_key, expiration_minutes)
            return JsonResponse(code="00", msg = "Merchant JWT token generated successfully", data={"token": token})
        except Exception as e:
            logger.error(f"GENERATE MERCHANT JWT TOKEN FAILED:: REASON ={e}")
            return JsonResponse(code="06" , msg = "Unable to generate merchant JWT token, please try again")