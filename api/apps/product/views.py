from django.db import IntegrityError
from apps.product.serializers import DataPackageSerializer, TransactionSerializer, ValidateVendDataSerializer, ValidateVendVtuSerializer, ProductCategorySerializer, ProductSerializer
from apps.product.models import DataPackage , Transaction, ProductCategory, Product
from apps.merchant.models import Merchant
from rest_framework import viewsets
from django.db import transaction as db_transaction
from apps.provider import ProviderServiceManager
from apps.product.task import trigger_provider_requery_task
from django.db.models import Case, When, CharField, Value, Max, F, FloatField
from django.utils import timezone   
from config.helper import CustomAuthentication, JsonResponse, format_msisdn
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.cache import cache
import logging
from decimal import Decimal
logger = logging.getLogger(__name__)

# Cache TTL constants (in seconds)
CACHE_TTL_PRODUCT = 3600  # 1 hour - products rarely change
CACHE_TTL_PRODUCT_CATEGORY = 7200  # 2 hours - categories rarely change
CACHE_TTL_DATA_PACKAGE = 3600  # 1 hour - data packages rarely change
CACHE_TTL_MERCHANT_DISCOUNT = 300  # 5 minutes - discounts can change more frequently
CACHE_TTL_PRODUCT_LIST = 1800  # 30 minutes - product lists
# Create your views here.


class ProductApiView(viewsets.ViewSet):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]
    
    #******************************************************#
    #======= get product categories =======================#
    #******************************************************#
    def get_product_cats(self, request):
        try:
            cache_key = "product_categories_active"
            cached_data = cache.get(cache_key)
            
            if cached_data is not None:
                return JsonResponse(data=cached_data)
            
            queryset = ProductCategory.objects.filter(is_active=True)
            serializer = ProductCategorySerializer(queryset, many=True)
            data = serializer.data
            
            # Cache for 2 hours
            cache.set(cache_key, data, CACHE_TTL_PRODUCT_CATEGORY)
            return JsonResponse(data=data)
        except Exception as e:
            logger.error(f"GET PRODUCT CAT  FAILED:: REASON ={e}")
            return JsonResponse(code="06" , msg = "Unable to retrieve categories, please try again")

    
    #******************************************************#
    #======= get products ================================#
    #******************************************************#
    def get_products(self, request):
        try:
            category_code = request.query_params.get("category_code")
            if not category_code:
                return JsonResponse(code="02", msg="category_code is required")   
            
            cache_key = f"products_category_{category_code}"
            cached_data = cache.get(cache_key)
            
            if cached_data is not None:
                return JsonResponse(data=cached_data)
            
            queryset = Product.objects.filter(category__category_code=category_code, is_active=True)
            if len(queryset) == 0:
                return JsonResponse(code="03", msg="No products found")
            
            serializer = ProductSerializer(queryset, many=True)
            data = serializer.data
            
            # Cache for 30 minutes
            cache.set(cache_key, data, CACHE_TTL_PRODUCT_LIST)
            return JsonResponse(data=data)
        except Exception as e:
            logger.error(f"GET PRODUCTS  FAILED:: REASON ={e}")
            return JsonResponse(code="06" , msg = "Unable to retrieve products, please try again")
    
    
    #******************************************************#
    #==================== GET LIST OF DATA BUNDLE =========#
    #******************************************************#
    def get_data_bundle(self, request):
        try:
            product_code = request.query_params.get("product_code")
            if not product_code:
                return JsonResponse(code="02", msg="product_code is required")
            
            cache_key = f"data_bundles_{product_code}"
            cached_data = cache.get(cache_key)
            
            if cached_data is not None:
                return JsonResponse(code="00", data=cached_data)
            
            bundles = DataPackage.objects.select_related('product').filter(
                product__product_code=product_code, is_active=True
            )
            if len(bundles) == 0:
                return JsonResponse(code="03", msg="No data bundle found")
            
            serializer = DataPackageSerializer(bundles, many=True)
            data = serializer.data
            
            # Cache for 1 hour
            cache.set(cache_key, data, CACHE_TTL_DATA_PACKAGE)
            return JsonResponse(code="00", data=data)
        except Exception as e:
            logger.error(f"FAILE GETTING BUNDLES AS::={e}")
            return JsonResponse(code="02", msg="Invalid payload")



    #******************************************************#
    #=============== VEND VTU =============================#
    #******************************************************#
    def vend_vtu(self, request):
        try:
            # Validate request
            validation_result = self._validate_vend_request(request, ValidateVendVtuSerializer)
            if validation_result:
                return validation_result
            
            # Extract data
            product_code, phone_number, merchant_ref = self._extract_vend_data(request)
            amount = Decimal(request.data.get("amount"))
            
            # Validate amount
            if amount <= 0:
                return JsonResponse(code="02", msg="Amount must be greater than 0")
            
            # Validate product
            product_result = self._validate_product(product_code, "AIRTIME")
            if isinstance(product_result, JsonResponse):
                return product_result
            product, product_category_code = product_result
            
            # Get merchant with discount
            merchant_result = self._get_merchant_with_discount(request.user.id, product_code)
            if isinstance(merchant_result, JsonResponse):
                return merchant_result
            merchant = merchant_result
            
            # Check transaction limit
            merchant = self._check_and_reset_transaction_limit(merchant)
            if isinstance(merchant, JsonResponse):
                return merchant
            
            # Calculate discounted amount
            discounted_amount = self._calculate_discounted_amount(merchant, amount)
            
            # Get provider account
            provider_account = product.preferred_provider_account
            provider_code = provider_account.provider.provider_code
            validation_result = self._validate_provider_code(provider_code)
            if validation_result:
                return validation_result
            
            # Debit and create transaction
            txn_result = self._debit_and_create_transaction(
                merchant, amount, discounted_amount, phone_number,
                product_code, product_category_code, merchant_ref, product,
                f"Airtime vending N{amount} for {phone_number}"
            )
            if isinstance(txn_result, JsonResponse):
                return txn_result
            txn = txn_result
            
            # Send for vending
            logger.info(f"{product_code} VEND VTU REQUEST:: MSISDN={phone_number}, AMOUNT={amount}, PRODUCTCODE={product_code}")
            response = ProviderServiceManager.vend(provider_account, phone_number, amount, product_code)
            
            # Handle response
            return self._handle_provider_response(response, txn, merchant)
            
        except Exception as e:
            logger.error(f"VEND VTU FAILED:: REASON={e}", exc_info=True)
            return JsonResponse(code="06", msg="Unable to vend vtu, please try again")





    #******************************************************#
    #=================== VEND DATA ========================#
    #******************************************************#
    def vend_data(self, request):
        try:
            # Validate request
            validation_result = self._validate_vend_request(request, ValidateVendDataSerializer)
            if validation_result:
                return validation_result
            
            # Extract data
            product_code, phone_number, merchant_ref = self._extract_vend_data(request)
            data_code = request.data.get("data_code")
            
            # Validate product
            product_result = self._validate_product(product_code, "DATA")
            if isinstance(product_result, JsonResponse):
                return product_result
            product, product_category_code = product_result
            
            # Check data bundle (with caching)
            cache_key = f"data_package_{product_code}_{data_code}"
            databundle = cache.get(cache_key)
            
            if not databundle:
                try:
                    databundle = DataPackage.objects.get(
                        product_code=product_code, 
                        data_code=data_code, 
                        is_active=True
                    )
                    # Cache for 1 hour
                    cache.set(cache_key, databundle, CACHE_TTL_DATA_PACKAGE)
                except DataPackage.DoesNotExist:
                    return JsonResponse(code="02", msg="No data bundle found")
            
            bundle_amount = Decimal(databundle.amount)
            
            # Get merchant with discount
            merchant_result = self._get_merchant_with_discount(request.user.id, product_code)
            if isinstance(merchant_result, JsonResponse):
                return merchant_result
            merchant = merchant_result
            
            # Check transaction limit
            merchant = self._check_and_reset_transaction_limit(merchant)
            if isinstance(merchant, JsonResponse):
                return merchant
            
            # Calculate discounted amount
            discounted_amount = self._calculate_discounted_amount(merchant, bundle_amount)
            
            # Get provider account
            provider_account = product.preferred_provider_account
            provider_code = provider_account.provider.provider_code
            validation_result = self._validate_provider_code(provider_code)
            if validation_result:
                return validation_result
            
            # Debit and create transaction
            txn_result = self._debit_and_create_transaction(
                merchant, bundle_amount, discounted_amount, phone_number,
                product_code, product_category_code, merchant_ref, product,
                f"Data vending and {databundle.description}"
            )
            if isinstance(txn_result, JsonResponse):
                return txn_result
            txn = txn_result
            
            # Send for vending
            logger.info(
                f"VEND DATA REQUEST:: MSISDN={phone_number}, AMOUNT={bundle_amount}, "
                f"PRODUCTCODE={product_code}, DATACODE={databundle.data_code}, TARIF={databundle.tariff_id}"
            )
            response = ProviderServiceManager.vend(
                provider_account, phone_number, bundle_amount, product_code, 
                databundle.data_code, databundle.tariff_id
            )
            
            # Handle response
            return self._handle_provider_response(response, txn, merchant)
            
        except Exception as e:
            logger.error(f"VEND DATA FAILED:: REASON={e}", exc_info=True)
            return JsonResponse(code="06", msg="Unable to vend data, please try again")




    #******************************************************#
    #========= Common Helper Methods for Vending ==========#
    #******************************************************#
    
    def _validate_vend_request(self, request, serializer_class):
        """Validate vend request payload"""
        serializer = serializer_class(data=request.data)
        if not serializer.is_valid():
            return JsonResponse(code="02", msg="Invalid request payload", data=serializer.errors, status=400)
        return None
    
    def _extract_vend_data(self, request):
        """Extract common data from vend request"""
        product_code = request.data.get("product_code")
        phone_number = format_msisdn(request.data.get("phone_number"))
        merchant_ref = request.data.get("merchant_ref")
        return product_code, phone_number, merchant_ref
    
    def _validate_product(self, product_code, expected_category):
        """Validate product exists, is active, and matches expected category"""
        cache_key = f"product_{product_code}"
        cached_product = cache.get(cache_key)
        
        if cached_product:
            product, product_category_code = cached_product
        else:
            product = Product.objects.filter(
                product_code=product_code,
                is_active=True
            ).select_related(
                "category", 
                "preferred_provider_account__provider"
            ).only(
                "id", "description", "is_active", 
                "category__category_code",
                "preferred_provider_account__id",
                "preferred_provider_account__provider__id",
                "preferred_provider_account__provider__provider_code"
            ).first()
            
            if not product:
                return JsonResponse(code="02", msg=f"Product {product_code} is not active")
            
            product_category_code = product.category.category_code
            # Cache product data for 1 hour
            cache.set(cache_key, (product, product_category_code), CACHE_TTL_PRODUCT)
        
        logger.info(f"REQUEST PRODUCT CATEGORY:: {product_category_code}")
        
        if product_category_code != expected_category:
            category_name = "Airtime" if expected_category == "AIRTIME" else "Data"
            return JsonResponse(code="02", msg=f"This product code {product_code} is not for {category_name}")
        
        return product, product_category_code
    
    def _get_merchant_with_discount(self, user_id, product_code):
        """Get merchant with discount information for the product"""
        cache_key = f"merchant_discount_{user_id}_{product_code}"
        cached_merchant = cache.get(cache_key)
        
        #if cached_merchant:
        #    merchant = cached_merchant
        #else:
        merchant = Merchant.objects.filter(user_id=user_id).annotate(
            _discount_value=Max(
                Case(
                    When(
                        merchant_discounts__product__product_code=product_code, 
                        merchant_discounts__is_active=True, 
                        then=F('merchant_discounts__discount_value')
                    ),
                    default=Value('0'),
                    output_field=FloatField()
                )
            ),
            _discount_type=Max(
                Case(
                    When(
                        merchant_discounts__product__product_code=product_code, 
                        merchant_discounts__is_active=True, 
                        then=F('merchant_discounts__discount_type')
                    ),
                    default=Value(None),
                    output_field=CharField()
                )
            )
        ).only(
            "id", "current_balance", "daily_tranx_limit", 
            "today_tranx_value", "today_tranx_date"
        ).first()
        
        if not merchant:
            logger.error(f"MERCHANT NOT FOUND FOR USER:: {user_id}")
            return JsonResponse(code="02", msg="Merchant not found")
        
        # Cache merchant with discount for 5 minutes (discounts can change)
        cache.set(cache_key, merchant, CACHE_TTL_MERCHANT_DISCOUNT)
    
        logger.info(
            f"REQUEST PRODUCT {product_code}:: "
            f"DISCOUNT_TYPE={merchant._discount_type}, "
            f"DISCOUNT_VALUE={merchant._discount_value} ::MERCHANT {merchant}"
        )
        
        return merchant
    
    def _check_and_reset_transaction_limit(self, merchant):
        """Check and reset transaction limit if needed"""
        merchant_check_limit = self.check_transaction_limit(merchant)
        if merchant_check_limit == False:
            return JsonResponse(code="05", msg="Your daily transaction limit is exceeded", data=[], status=400)
        
        # If transaction limit was reset (new day), invalidate merchant discount cache
        # to ensure fresh balance data is fetched
        if merchant_check_limit.today_tranx_date != merchant.today_tranx_date:
            from apps.product.cache_utils import invalidate_merchant_discount_cache
            # Invalidate all discount caches for this merchant (simplified - would need product_code list in production)
            logger.info(f"Transaction limit reset for merchant {merchant.id}, cache will refresh on next request")
        
        return merchant_check_limit
    
    def _calculate_discounted_amount(self, merchant, amount):
        """Calculate commission and discounted amount"""
        discount_type = merchant._discount_type
        discount_value = Decimal(merchant._discount_value or 0)
        commission_amount = Decimal(0)
        
        if discount_type:
            if discount_type == 'fixed':
                commission_amount = discount_value
            else:
                # Percentage discount
                commission_amount = (discount_value / 100) * amount
        
        discounted_amount = amount - commission_amount
        return discounted_amount
    
    def _validate_provider_code(self, provider_code):
        """Validate provider code is set"""
        if not provider_code or provider_code == "":
            return JsonResponse(code="02", msg="No route set for sending vend")
        return None
    
    def _debit_and_create_transaction(self, merchant, amount, discounted_amount, 
                                     phone_number, product_code, product_category_code, 
                                     merchant_ref, product, description):
        """Debit merchant balance and create transaction atomically"""
        try:
            with db_transaction.atomic():
                merchant_obj = merchant.debit_balance(discounted_amount)
                # Get product_category object from product
                product_category = product.category
                txn = Transaction.objects.create(
                    amount=amount,
                    discount_amount=discounted_amount,
                    balance_before=merchant_obj.balance_before,
                    balance_after=merchant_obj.current_balance,
                    beneficiary_account=phone_number,
                    product=product,
                    product_category=product_category,
                    description=description,
                    merchant_ref=merchant_ref,
                    status="Pending",
                    merchant=merchant
                )
                return txn
        except ValueError as e:
            logger.error(f"FAILED TO DEBIT MERCHANT BALANCE:: REASON={e}")
            return JsonResponse(code="04", msg=str(e))
        except IntegrityError as e:
            logger.error(f"FAILED TO CREATE TRANSACTION:: REASON={e}")
            return JsonResponse(code="06", msg="Duplicate transaction, please try again")
        except Exception as e:
            logger.error(f"FAILED TO CREATE TRANSACTION:: REASON={e}")
            return JsonResponse(code="06", msg="Unable to process transaction, please try again")
    
    def _handle_provider_response(self, response, txn, merchant):
        """Handle provider response and update transaction"""
        status_code = "06"
        status_message = "Unable to process transaction, please try again"
        
        with db_transaction.atomic():
            # Refresh and select related product for serializer
            txn = Transaction.objects.select_related('product').get(id=txn.id)
            txn.provider_desc = response.get("responseMessage", "Unknown response")
            txn.provider_ref = response.get("provider_ref", "")
            
            if response.get("responseCode") == "00":
                txn.status = "Success"
                status_code = "00"
                status_message = 'Transaction successful'
            elif response.get("responseCode") == "80":  # for timeout try requery
                status_message = "Awaiting response from provider"
                txn.status = "Processing"
                #trigger_provider_requery_task.delay(txn.id)  # run in background
            else:
                merchant.credit_balance(txn.discount_amount)
                txn.status = "Failed"
                txn.is_reverse = True
                txn.reversed_at = timezone.now()
                if response.get("responseCode") == "08":
                    status_message = "Invalid MSISDN"
            
            txn.save(update_fields=[
                'status', 'updated_at', 'provider_ref', 'provider_desc', 
                'is_reverse', 'reversed_at'
            ])
        
        serializer = TransactionSerializer(txn)
        return JsonResponse(code=status_code, data=serializer.data, msg=status_message)

  
   
    #******************************************************#
    #Requery transaction
    #******************************************************#
    def get_transaction_by_client_ref(self, request):
        try:
            merchant = request.user.merchant
            merchant_ref = request.data.get("merchant_ref")
            if not merchant_ref:
                return JsonResponse(code="02", msg="Invalid payload")
            tranx = Transaction.objects.select_related('product').filter(
                merchant_ref=merchant_ref, merchant_id=merchant.id
            ).first()
            if not tranx:
                return JsonResponse(code="03", msg="No record found")
            serializer = TransactionSerializer(tranx)
            return JsonResponse(code="00",data=serializer.data)
        except Exception as e:
            logger.error(f"FAILE GETTING TRANSACTIONS AS:: {str(e)}")
            return JsonResponse(code="02", msg="Invalid payload")



    #******************************************************#
    #check merchant daily transaction limit
    #******************************************************#
    def check_transaction_limit(self,merchant):
        today = timezone.now().date()
        if  merchant.today_tranx_date != today:
            merchant.today_tranx_date = today
            merchant.today_tranx_value = 0 #reset daily transactions
        #check daily transaction limit
        if int(merchant.today_tranx_value) >= int(merchant.daily_tranx_limit):
            return False
        return merchant



    #******************************************************#
    #======= reverse timeout and unreversed transaction ===#
    #******************************************************#
    def cron_reverse_timeout_unreversed_transaction(self,request):
        two_minutes_ago = timezone.now() - timezone.timedelta(minutes=2)
        tranxs = Transaction.objects.filter(is_reverse=False, status="Pending",created_at__lte=two_minutes_ago)[:100]
        logger.info(f"CRON TRANXS:: COUNT={len(tranxs)}")
        for tx in tranxs:
            try:
                with db_transaction.atomic():
                    merchant = Merchant.objects.select_for_update().get(id=tx.merchant.id)
                    merchant.current_balance = float(merchant.current_balance) + float(tx.discount_amount or 0)
                    merchant.save()
                    logger.info(f"CRON MERCHANT SAVED:: {merchant.id} :: BALANCE={merchant.current_balance} :: PREV BAL={merchant.previous_balance} :: DISCOUNT={tx.discount_amount} :: REF={tx.tranx_ref}")
                    tx.previous_bal = merchant.previous_balance
                    tx.current_bal = merchant.current_balance
                    tx.prev_bal_bfo_txn = merchant.current_balance
                    tx.status = "Failed"
                    tx.provider_desc = "Transaction timed out"
                    tx.is_reverse = True
                    tx.reversed_at = timezone.now() 
                    tx.save()
                    logger.info(f"CRON TRANSACTION SAVED:: :: REF={tx.tranx_ref} :: STATUS={tx.status} :: REVERSED AT={tx.reversed_at}")
            except Exception as e:
                logger.error(f"CRON FAILED TO REVERSE TRANSACTION ID={tx.id} REASON={e}")
        return JsonResponse(code="00", msg="Cron job completed successfully")
    
    #******************************************************#
    #======= get permission ================================#
    #******************************************************#
    def get_permissions(self):
        if self.action == 'cron_reverse_timeout_unreversed_transaction':
            permission_classes = [AllowAny]
        else:
            #permission_classes = [IsAuthenticated]
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]  

   