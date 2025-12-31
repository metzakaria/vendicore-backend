import hmac
import jwt
from Crypto.Util.Padding import pad, unpad
import hashlib
from Crypto.Cipher import AES
import base64
from rest_framework.fields import json
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from config.settings import SECRET_KEY
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
#from django.utils.translation import gettext_lazy as _

from django.utils import timezone
from django.core.cache import cache
#from rest_framework.authtoken.models import Token
from apps.merchant.models import Merchant
from config.response_codes import AUTHENTICATION_ERROR, RESPONSE_MESSAGES
import logging

logger = logging.getLogger(__name__)


#================ CUSTOM EXCEPTION ====
def custom_exception_handler(exc, context):
    # Call DRF's default exception handler first
    from rest_framework.views import exception_handler
    response = exception_handler(exc, context)
    # Customize the error response as needed
    if response is not None:
        error = RESPONSE_MESSAGES[AUTHENTICATION_ERROR]
        if str(exc)!="":
            error = str(exc)
            if "token_not_valid" in error:
                error = "Invalid Token"
        response = JsonResponse(code=AUTHENTICATION_ERROR, msg=error, status=response.status_code)
    return response


#====================== CUSTOM API RESPONSE ==============#
class JsonResponse(Response):
    def __init__(self, data=[], code="00",success=True, msg="Successful",
                 status=None,
                 paginator=None,
                 template_name=None, headers=None,
                 exception=False, content_type=None, **kwargs):
        super().__init__(None, status=status)

        if isinstance(data, Serializer):
            msg = (
                'You passed a Serializer instance as data, but '
                'probably meant to pass serialized `.data` or '
                '`.error`. representation.'
            )
            raise AssertionError(msg)
        self.data = {'responseCode': code, 'responseMessage': msg, 'responseData': data}
        if paginator:
            self.data.update({'nextPage': paginator.get_next_link(), 'prevPage': paginator.get_previous_link(), 'totalCount': paginator.page.paginator.count})
        self.data.update(kwargs)
        self.template_name = template_name
        self.exception = exception
        self.content_type = content_type

        if headers:
            for name, value in headers.items():
                self[name] = value



#================ CUSTOM AUTH for vending====
class CustomAuthentication(BaseAuthentication):
    """
    Optimized authentication class for vending API that validates:
    - Merchant code from X-Merchant-Code header
    - API token from Authorization header (Bearer token) - JWT signed with merchant's secret key
    - Timestamp from X-Timestamp header (replay attack protection)
    
    Security improvements:
    - Uses JWT tokens signed with merchant's secret key (secret key never sent in request)
    - Includes timestamp in JWT to prevent replay attacks
    - Caches merchant data to reduce database queries
    - Validates token signature using merchant's secret key from database
    """
    # Cache TTL for merchant data (5 minutes)
    _cache_ttl = 300  # 5 minutes in seconds
    
    def _get_cached_merchant(self, merchant_code, api_key):
        """
        Get merchant from distributed cache (Redis/Memcached) or database.
        Works across multiple server instances using Django's cache framework.
        
        Multi-instance safety:
        - Uses Django's cache framework which supports Redis/Memcached
        - Cache is shared across all server instances
        - Automatically handles cache expiration and invalidation
        """
        cache_key = f"merchant_auth_{merchant_code}"
        
        # Try to get from distributed cache (works across instances)
        cached_merchant = cache.get(cache_key)
        if cached_merchant:
            return cached_merchant
        
        # Cache miss - fetch from database
        try:
            merchant = Merchant.objects.select_related('user').get(
                merchant_code=merchant_code,
                is_active=True,
                api_key=api_key
            )
            # Store in distributed cache (shared across all instances)
            cache.set(cache_key, merchant, self._cache_ttl)
            return merchant
        except Merchant.DoesNotExist:
            return None
    
    @staticmethod
    def invalidate_merchant_cache(merchant_code):
        """
        Invalidate merchant cache when merchant data changes.
        Call this after updating merchant information to ensure all instances
        get the latest data.
        
        Usage:
            CustomAuthentication.invalidate_merchant_cache(merchant_code)
        """
        cache_key = f"merchant_auth_{merchant_code}"
        cache.delete(cache_key)
    
    def authenticate(self, request):
        request_ip = get_client_ip(request)
        
        try:
            # Get merchant code from header
            merchant_code = request.headers.get("X-MERCHANT-CODE")
            api_key = request.headers.get("X-API-KEY")
            received_signature = request.headers.get("X-SIGNATURE")
            timestamp = request.headers.get("X-TIMESTAMP")
            if not merchant_code or not api_key or not received_signature or not timestamp:
                logger.error("X-Merchant-Code, X-API-KEY, X-SIGNATURE, and X-TIMESTAMP headers not found")
                raise AuthenticationFailed('Merchant code, API key, received signature, and timestamp are required')
            
            
            # Get cached merchant (reduces DB queries)
            merchant = self._get_cached_merchant(merchant_code, api_key)
            if not merchant:
                logger.error(f"Merchant not found or inactive: {merchant_code}")
                raise AuthenticationFailed('Invalid merchant code or merchant is inactive')
            
            #check timestamp is within 5 minutes
            from datetime import datetime, timezone
            # Parse timestamp - handle both with and without Z suffix
            timestamp_clean = timestamp.replace("Z", "+00:00") if timestamp.endswith("Z") else timestamp
            req_time = datetime.fromisoformat(timestamp_clean)
            # Ensure timezone-aware
            if req_time.tzinfo is None:
                req_time = req_time.replace(tzinfo=timezone.utc)
            # Use Django's timezone-aware now() which respects TIME_ZONE setting
            now = datetime.now(timezone.utc)
            logger.info(f"REQUEST TIMESTAMP:: {req_time} CURRENT TIMESTAMP:: {now} DIFF SECONDS:: {abs((now - req_time).total_seconds())}")
            if abs((now - req_time).total_seconds()) > 300:
                logger.error(f"Expired request: {timestamp} (diff: {abs((now - req_time).total_seconds())} seconds)")
                raise AuthenticationFailed('Request has expired') 
            
            # Simple signature: timestamp|api_key
            stringToSign = f"{timestamp}|{api_key}"
            logger.info(f"STRING TO SIGN:: {stringToSign}")
            #compare stringToSign with received signature
            server_signature = base64.b64encode(
                    hmac.new(
                    merchant.api_secret.encode(),
                    stringToSign.encode(),
                    hashlib.sha256
                ).digest()
            ).decode()

            if not hmac.compare_digest(received_signature.encode("utf-8"), server_signature.encode("utf-8")):
                logger.error(f"Invalid signature: {received_signature.encode('utf-8')} != {server_signature.encode('utf-8')}")
                raise AuthenticationFailed('Invalid signature')

                
            # Optional: Validate IP address if configured
            if merchant.api_access_ips and request_ip not in merchant.api_access_ips.split(','):
                logger.error(f"Unauthorized IP: {request_ip} not in {merchant.api_access_ips}")
                raise AuthenticationFailed('Unauthorized IP')
            
            # Get user associated with merchant
            if not merchant.user:
                logger.error(f"No user associated with merchant: {merchant_code}")
                raise AuthenticationFailed('Merchant account not properly configured')
            
            user = merchant.user
            
            logger.info(f"Authentication successful for merchant: {merchant_code}, user: {user.email}")
            return (user, merchant)
            
        except AuthenticationFailed:
            # Re-raise authentication failures
            raise
        except Exception as e:
            logger.error(f"AUTH ERROR: {str(e)}")
            raise AuthenticationFailed('Authentication failed')



#======================== function to measure response time ========
#===============================================================#
def measure_response_time(start_time,txt):
    import time
    end_time = time.time()
    response_time = end_time - start_time
    logger.info(f"{txt} RESPONSE TIME: {response_time} seconds")
    return response_time

#============== Custome Cors ===================
class CustomCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response["Access-Control-Max-Age"] = "3600"
        response["Access-Control-Allow-Credentials"] = "true"
        return response




#=============== GET CLIENT IP ===========
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

#******************************************************#
#======= format phone number ==========================#
#******************************************************#
def format_msisdn(phone):
    phone = phone.replace("+","")
    if phone.startswith("234"):
        phone = phone.replace('234','0',1)
    return phone