import os 
import requests
import base64
import random
import json
import datetime
import xmltodict
import logging
import re

logger = logging.getLogger(__name__)

"""
******************************************
********* Provider: SIM Server  **********
******************************************

This service is for Sim Server  Provider
to be able to send Airtime and Data purchase 
to the provider

"""
class SimServerProviderService():
    def __init__(self, receiver_phone, amount, data_code):
        self.url = os.environ.get("SIM_SERVER_PROVIDER_URL")
        self.receiver_phone = receiver_phone
        self.amount = amount
        self.data_code = data_code
        

    
    # send request to simserver provider
    def send_request(self):
        response = {}
        try:
            #payload for airtime vending
            payload = {
                "product_code" : self.data_code,
                "amount":  self.amount,
                "recipient": self.receiver_phone,
            }
 
            header = {
                "Content-Type"          :       "application/json",
			    "Accept"                :       "application/json"
            }
            logger.info(f"RAW SIMSERVER REQUEST PAYLOAD:::{payload} :::: HEADER::{header}")
            
            resp = requests.post(self.url,data=payload, headers=header, timeout=30).content
            logger.info(f"RAW SIMSERVER RESPONSE:::{resp}")
            json_resp = json.loads(resp)

            response["responseCode"] = "90"
            response["responseMessage"] = json_resp["message"]
            response["provider_ref"] = ""
            response["provider_avail_bal"] = "0"
            if json_resp["status"] == True:
                response["responseCode"] = "00"
        except requests.Timeout:
            logger.error(f"FAILED SIMSERVER REQUEST TIMEOUT")
            response["responseCode"] = "90"
            response["responseMessage"] = "Request timeout after 30 seconds"
        except Exception as e:
            logger.error(f"FAILED SIMSERVER REQUEST:, REASON::{e}")
            response["responseCode"] = "90"
            response["responseMessage"] = str(e)
        return response


