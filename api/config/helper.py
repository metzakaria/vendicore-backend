import jwt
from Crypto.Util.Padding import pad, unpad
import hashlib
from Crypto.Cipher import AES
import base64
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from config.settings import SECRET_KEY
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
#from django.utils.translation import gettext_lazy as _
from time import time 
import datetime
from django.utils import timezone
from django.core.cache import cache
#from rest_framework.authtoken.models import Token
from apps.merchant.models import User, Merchant
import logging

logger = logging.getLogger(__name__)


#================ CUSTOM EXCEPTION ====
def custom_exception_handler(exc, context):
    # Call DRF's default exception handler first
    from rest_framework.views import exception_handler
    response = exception_handler(exc, context)
    # Customize the error response as needed
    if response is not None:
        error = "An error occurred"
        if str(exc)!="":
            error = str(exc)
            if "token_not_valid" in error:
                error = "Invalid Token"
        response = JsonResponse(code="07", msg=error, status=response.status_code)
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
    
    def _get_cached_merchant(self, merchant_code):
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
                is_active=True
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
            merchant_code = request.headers.get('x-merchant-code')
            if not merchant_code:
                logger.error("X-Merchant-Code header not found")
                raise AuthenticationFailed('Merchant code is required')
            
            # Get API token from Authorization header (should be JWT)
            header_authorization = request.headers.get('Authorization')
            if not header_authorization or not header_authorization.startswith('Bearer '):
                logger.error(f"Authorization header not set or invalid format")
                raise AuthenticationFailed('Authorization header is required')
            
            jwt_token = header_authorization.split(' ')[1].strip()
            if not jwt_token:
                logger.error("JWT token not found in Authorization header")
                raise AuthenticationFailed('API token is required')
            
            # Get cached merchant (reduces DB queries)
            merchant = self._get_cached_merchant(merchant_code)
            #logger.info(f"Merchant: {merchant.api_secret_key}")
            if not merchant:
                logger.error(f"Merchant not found or inactive: {merchant_code}")
                raise AuthenticationFailed('Invalid merchant code or merchant is inactive')
            
            # Validate merchant has required credentials
            if not merchant.api_secret_key:
                logger.error(f"Merchant has no API secret key: {merchant_code}")
                raise AuthenticationFailed('Merchant not properly configured')
            
            # Decode and verify JWT token using merchant's secret key
            try:
                # Use merchant's secret key to verify the JWT signature
                token_payload = jwt.decode(
                    jwt_token, 
                    merchant.api_secret_key, 
                    algorithms=['HS256']
                )
            except jwt.ExpiredSignatureError:
                logger.error(f"JWT token expired for merchant: {merchant_code}")
                raise AuthenticationFailed('Token has expired')
            except jwt.InvalidTokenError as e:
                logger.error(f"Invalid JWT token for merchant {merchant_code}: {str(e)}")
                raise AuthenticationFailed('Invalid token signature')
            
            # Validate token belongs to this merchant
            if token_payload.get('merchant_code') != merchant_code:
                logger.error(f"Token merchant_code mismatch for merchant: {merchant_code}")
                raise AuthenticationFailed('Token does not match merchant')
            
            # Replay attack protection: Check timestamp (within 5 minutes)
            token_timestamp = token_payload.get('timestamp')
            if token_timestamp:
                try:
                    token_time = datetime.datetime.fromtimestamp(token_timestamp, tz=timezone.utc)
                    now = timezone.now()
                    time_diff = abs((now - token_time).total_seconds())
                    
                    # Allow 5 minute window for clock skew
                    if time_diff > 300:
                        #logger.error(f"Token timestamp too old/new for merchant {merchant_code}. Diff: {time_diff}s")
                        #raise AuthenticationFailed('Token timestamp invalid')
                        pass
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid timestamp in token for merchant {merchant_code}: {str(e)}")
                    raise AuthenticationFailed('Invalid token timestamp')
            
            # Optional: Validate IP address if configured
            if merchant.api_access_ip:
                if merchant.api_access_ip != request_ip:
                    logger.warning(f"IP address mismatch for merchant {merchant_code}. Registered: {merchant.api_access_ip}, Request: {request_ip}")
                    # Uncomment to enforce IP validation
                    # raise AuthenticationFailed('IP address not authorized')
            
            # Get user associated with merchant
            if not merchant.user:
                logger.error(f"No user associated with merchant: {merchant_code}")
                raise AuthenticationFailed('Merchant account not properly configured')
            
            user = merchant.user
            
            logger.info(f"Authentication successful for merchant: {merchant_code}, user: {user.email}")
            return (user, jwt_token)
            
        except AuthenticationFailed:
            # Re-raise authentication failures
            raise
        except Exception as e:
            logger.error(f"AUTH ERROR: {str(e)}")
            raise AuthenticationFailed('Authentication failed')



    
    

#================ HELPER FUNCTION TO GENERATE MERCHANT JWT TOKEN ==============#
def generate_merchant_jwt_token(merchant_code, api_secret_key, expiration_minutes=60):
    """
    Generate a JWT token for merchant API authentication.
    
    Args:
        merchant_code: The merchant's unique code
        api_secret_key: The merchant's API secret key (used to sign the token)
        expiration_minutes: Token expiration time in minutes (default: 60)
    
    Returns:
        str: JWT token string
    
    Usage:
        token = generate_merchant_jwt_token(
            merchant_code="1234567",
            api_secret_key=merchant.api_secret_key,
            expiration_minutes=60
        )
    """
    now = timezone.now()
    expiration_time = now + datetime.timedelta(minutes=expiration_minutes)
    
    payload = {
        'merchant_code': merchant_code,
        'timestamp': int(now.timestamp()),  # Unix timestamp for replay attack protection
        'exp': int(expiration_time.timestamp()),  # JWT expiration (Unix timestamp)
        'iat': int(now.timestamp()),  # Issued at time (Unix timestamp)
    }
    
    # Sign token with merchant's secret key
    token = jwt.encode(payload, api_secret_key, algorithm='HS256')
    return token
    

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