from .models import DataPackage , Transaction, Product
from apps.provider.models import Provider
from apps.provider import ProviderServiceManager
from apps.merchant.models import Merchant
from django.db import transaction as db_transaction
import datetime
from django.db.models import  F
import logging
from celery import shared_task
from django.core.cache import cache 
from celery.utils.log import get_task_logger
from django.utils import timezone
from datetime import timedelta
from config.response_codes import SUCCESS, PENDING, FAILED, INVALID_MSISDN, RESPONSE_MESSAGES
from config.helper import measure_response_time
import time
#logger = get_task_logger(__name__)

logger = logging.getLogger(__name__)

LOCK_EXPIRE = 60  # seconds
#******************************************************#
#======= Requery pending transactions from provider =====#
#******************************************************#
@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def trigger_provider_requery_task(self, transaction_id: int):
    """
    Requery a pending transaction from the provider and update its status.
    
    Args:
        transaction_id: The ID of the transaction to requery
        
    Retries:
        - Up to 3 times with 60 seconds delay between retries
        - If still pending after retries, transaction remains in Processing status
    """
    
    lock_id = f"requery-lock-{transaction_id}"
    # Try to acquire lock
    acquire = cache.add(lock_id, "locked", LOCK_EXPIRE)
    if not acquire:
        logger.warning(f"Task already running for transaction {transaction_id}, skipping...")
        return
    
    start_time = time.time()
    try:
        txn = Transaction.objects.select_related(
            'product__preferred_provider_account__provider',
            'merchant'
        ).get(id=transaction_id)
        
        # Check if transaction is still pending/processing
        if txn.status not in ["Processing", "Pending"]:
            logger.info(f"Transaction {transaction_id} is no longer pending. Status: {txn.status}")
            return
        
        # Get provider account from transaction or product
        provider_account = txn.provider_account or txn.product.preferred_provider_account
        if not provider_account:
            logger.error(f"No provider account found for transaction {transaction_id}")
            return    
        #get product code
        product_code = txn.product.product_code    
        # Requery the provider
        logger.info(f"Requerying transaction {transaction_id} with provider {provider_account.provider.provider_code}")
        response = ProviderServiceManager.requery(
            provider_account=provider_account,
            merchant_ref=txn.merchant_ref,
            product_code=product_code
        )
        
        response_code = response.get("responseCode")
        response_message = response.get("responseMessage", "")
        provider_ref = response.get("provider_ref", txn.provider_ref)
        
        # Update transaction based on response
        with db_transaction.atomic():
            txn = Transaction.objects.select_for_update().get(id=transaction_id)
            
            if response_code == SUCCESS:
                # Transaction succeeded
                txn.status = "Success"
                txn.provider_ref = provider_ref
                txn.provider_desc = response_message
                txn.save(update_fields=['status', 'provider_ref', 'provider_desc', 'updated_at'])
                logger.info(f"Transaction {transaction_id} updated to Success")
                
            elif response_code == PENDING:
                # Still pending, retry if we have retries left
                if self.request.retries < self.max_retries:
                    logger.info(f"Transaction {transaction_id} still pending, retrying... (attempt {self.request.retries + 1}/{self.max_retries})")
                    raise self.retry(countdown=20)  # Retry after 60 seconds
                else:
                    # Max retries reached, keep as Processing
                    txn.provider_desc = f"{response_message} (Max retries reached)"
                    txn.save(update_fields=['provider_desc', 'updated_at'])
                    logger.warning(f"Transaction {transaction_id} still pending after max retries")
                    
            else:
                # Transaction failed or error occurred
                # Refund merchant if not already reversed
                if not txn.is_reverse:
                    merchant = Merchant.objects.select_for_update().get(id=txn.merchant.id)
                    merchant.credit_balance(txn.discount_amount)
                    merchant.save()
                
                txn.status = "Failed"
                txn.provider_desc = response_message
                txn.is_reverse = True
                txn.reversed_at = timezone.now()
                
                txn.save(update_fields=[
                    'status', 'provider_desc', 'is_reverse', 
                    'reversed_at', 'updated_at'
                ])
                logger.info(f"Transaction {transaction_id} updated to Failed: {response_message}")
            measure_response_time(start_time,"TRIGGER PROVIDER REQUERY TASK")
    except Transaction.DoesNotExist:
        logger.error(f"Transaction {transaction_id} not found")
    except Exception as e:
        logger.error(f"Error requerying transaction {transaction_id}: {str(e)}", exc_info=True)
        # Retry on exception if we have retries left
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=20)
        else:
            logger.error(f"Max retries reached for transaction {transaction_id}")
            
            





#******************************************************#
#======= update pending transactions ============ =====#
#******************************************************#
@shared_task(bind=True)
def cron_reverse_timeout_unreversed_transaction(self):
    minutes_ago = timezone.now() - timezone.timedelta(minutes=5)
    #print("CRONTA=========================")
    tranxs = Transaction.objects.filter(
        is_reverse=False,
        status="Pending",
        created_at__lte=minutes_ago,
    )[:100]

    #logger.info(f"CRON TRANXS:: COUNT={tranxs.count()}")

    for tx in tranxs:
        try:
            # 🔒 Distributed row-level lock to avoid double processing
            with db_transaction.atomic():
                tx_locked = Transaction.objects.select_for_update().get(id=tx.id)

                if tx_locked.is_reverse or tx_locked.status != "Pending":
                    logger.info(f"SKIPPED already handled {tx_locked.id}")
                    continue

                merchant = Merchant.objects.select_for_update().get(id=tx_locked.merchant.id)
                merchant.credit_balance(tx_locked.discount_amount or 0)
                merchant.save()

                logger.info(f"CRON MERCHANT SAVED:: {merchant.id} :: BALANCE={merchant.current_balance}")

                tx_locked.status = "Failed"
                tx_locked.provider_desc = "Transaction timed out"
                tx_locked.is_reverse = True
                tx_locked.reversed_at = timezone.now()

                tx_locked.save(update_fields=[
                    'status', 'provider_desc', 'is_reverse',
                    'reversed_at', 'updated_at'
                ])

                logger.info(f"CRON TRANSACTION SAVED:: REF={tx_locked.merchant_ref}")
        except Exception as e:
            logger.error(f"CRON FAILED TO REVERSE TRANSACTION ID={tx.id} REASON={e}")