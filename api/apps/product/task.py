from .models import DataPackage , Transaction, Product
from apps.provider.models import Provider
from apps.merchant.models import Merchant
from django.db import transaction
import datetime
from django.db.models import  F
import logging
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from datetime import timedelta
import requests
#logger = get_task_logger(__name__)

logger = logging.getLogger(__name__)

#******************************************************#
#======= handle vend response in background============#
#******************************************************#
@shared_task
def bg_task_handle_vend_response(tranx_id: int, resp_obj: dict):
    try:
        tranx = Transaction.objects.get(id=tranx_id)
        logger.info(f"TRANX :::ID={tranx.id} : PRODUCTCODE={tranx.product_code} : AMOUNT={tranx.amount} : STATUS={tranx.status} : BENEFICIARY={tranx.beneficiary_account}")
        if resp_obj["responseCode"]=="00":
            try:
                provider_code = tranx.product.preferred_provider_code
                with transaction.atomic():
                    provider = Provider.objects.filter(provider_code=provider_code).select_for_update().first()
                    tranx.status="Success"
                    tranx.provider_ref = resp_obj["provider_ref"]
                    tranx.provider_desc = resp_obj["responseMessage"]
                    tranx.save()
                    #================
                    provider = Provider.objects.filter(provider_code=provider_code).select_for_update().first()
                    provider.available_balance = float(provider.available_balance)-float(tranx.amount)
                    provider.balance_at_provider = float(resp_obj["provider_avail_bal"])
                    provider.save()
                    logger.info(f" TRANX UPDETED :::ID={tranx.id} : PRODUCTCODE={tranx.product_code} : AMOUNT={tranx.amount} IS SUCCESS : BENEFICIARY={tranx.beneficiary_account}")
            except Exception as e:
                logger.error(f"FAILED TO UPDATE TRANX:::ID={tranx.id} PRODUCTCODE={tranx.product_code} REASON={e} : BENEFICIARY={tranx.beneficiary_account}")
        else:
            try:
                #merchant = tranx.merchant
                with transaction.atomic():
                    if not tranx.is_reverse: 
                        merchant = Merchant.objects.select_for_update().get(id=tranx.merchant.id)
                        #merchant.previous_balance = tranx.prev_bal_bfo_txn
                        merchant.current_balance =  float(merchant.current_balance) + tranx.discount_amount
                        merchant.save()
                    tranx.previous_bal =  merchant.previous_balance
                    tranx.current_bal =  merchant.current_balance
                    tranx.prev_bal_bfo_txn = merchant.current_balance
                    tranx.status="Failed"
                    #tranx.provider_ref = resp_obj["provider_ref"]
                    tranx.provider_desc = resp_obj["responseMessage"]
                    tranx.is_reverse = True 
                    tranx.reversed_at = datetime.datetime.today() 
                    tranx.save()
                    logger.info(f"FAILED TRANX :::ID={tranx.id} : PRODUCTCODE={tranx.product_code} : AMOUNT={tranx.amount} IS REVERSED : BENEFICIARY={tranx.beneficiary_account}")
            except Exception as e:
                logger.error(f"FAILED TO REVERSE TRANX:::TXID={tranx.id} PRODUCTCODE={tranx.product_code} REASON={e}")
    #except Transaction.DoesNotExist: 
    except Exception as e:
        logger.error(f"FAILED TO UPDATE RESPONSE AS TRANX WITH ID::TXID={tranx_id} WITH REASON= {str(e)}")


#******************************************************#
#======= handle cron reverse timeout unreversed transaction =====#
#******************************************************#
@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def trigger_provider_requery_task(self, transaction_id):
    try:
        txn = Transaction.objects.get(id=transaction_id)
        # Call provider requery API
        res = requests.get("https://provider.api/requery", params={"ref": txn.provider_ref}, timeout=10)
        data = res.json()

        if data.get("status") == "success":
            txn.status = "Success"
        elif data.get("status") == "failed":
            txn.status = "Failed"
            txn.merchant.credit_balance(txn.amount, source="Requery Refund")
        else:
            self.retry(countdown=60)  # retry again after 1 minute

        txn.provider_desc = data.get("message")
        txn.updated_at = timezone.now()
        txn.save(update_fields=["status", "provider_desc", "updated_at"])
    except Exception as e:
        raise self.retry(exc=e)