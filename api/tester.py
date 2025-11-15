#!/usr/bin/env python
import re
payload = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
                <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://hostif.vtm.prism.co.za/xsd">
                <soapenv:Header/><soapenv:Body>
                <xsd:vend>
                <xsd:origMsisdn>99999999</xsd:origMsisdn>
                <xsd:destMsisdn>33333333 9s</xsd:destMsisdn>
                <xsd:amount>50</xsd:amount>
                <xsd:sequence>009000</xsd:sequence>
                <xsd:tariffTypeId>1</xsd:tariffTypeId>
                <xsd:serviceproviderId>1</xsd:serviceproviderId>
                </xsd:vend></soapenv:Body></soapenv:Envelope>'''
xml_content = re.sub(r">\s+<", "><", payload)

print(xml_content)
exit()

import config.wsgi
#import datetime
from datetime import datetime, timedelta

from apps.provider.services import MTNNProviderService,AirtelProviderService
import secrets
from apps.product.models import Transaction
from Crypto.Cipher import DES3
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import hashlib
import base64
from Crypto.Cipher import AES
import json
import xmltodict
#from apps.provider.services import MTNNProviderService
#tranx = Transaction.objects.get(tranx_ref='bbda806d90304ae4be60168690761d7a')
#merchant = tranx.merchant
#print(merchant.__dict__)


import time 
current = time.time()
#time.sleep(3)
#current1 = time.time()
print("OHPYd2TvMhPSjmgKXFHLg7urKcp+epP8nQQcHcRe76M=")
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMiIsIm1hcmNoYW50X2NvZGUiOiI3OTAwODMxIiwiYXBpX3NlcmV0IjoiZDY1ZTg3ZjVhYTBiOWVjZmU3Mjk1ODFiZWI0ZDY2NTFlZWYzYTcwNDQ0ZDRlYTQ2IiwiZXhwIjoxNzE5NzgwNDEwfQ.687eyh0If287S1LeKnuyzgMu5IR5tHGdD4xmGHHDkyo.OHPYd2TvMhPSjmgKXFHLg7urKcp+epP8nQQcHcRe76M="

token_secrect = token.split(".")

token_ = ".".join(token_secrect[:3])
secret_ = token.replace(token_,"")[1:]
print(token_)

print(secret_)

#print(toke)
exit()
print(current)

#print(curtime)

#exit()
BLOCK_SIZE = 32 # Bytes

api_secret = secrets.token_hex(24)
#print(api_secret)
original_key = 'd65e87f5aa0b9ecfe729581beb4d6651eef3a70444d4ea46'
#original_key = "0123456789abcdef" * 6
key = hashlib.sha256(original_key.encode('utf8')).digest()

cipher = AES.new(key, AES.MODE_ECB)
msg = cipher.encrypt(pad(b'7900831|1688289697.841211', BLOCK_SIZE))
print(msg.hex())
msg1 = base64.b64encode(msg)
print(msg1)


decipher = AES.new(key, AES.MODE_ECB)
enc = base64.b64decode(msg1)
msg_dec = decipher.decrypt(enc)
print(unpad(msg_dec, BLOCK_SIZE))

#today  = datetime.today() + timedelta(hours=1)
#print(today)
exit()
response = MTNNProviderService("08069335817",100,1).send_request()
#response = AirtelProviderService("08069335817",100,"AIRTELDATA")
print(response)
'''
resp = """<soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\"><soap:Body><ns2:requestTopupResponse xmlns:ns2=\"http://external.interfaces.ers.seamless.com/\"><return><ersReference>2023061017494635404502669</ersReference><resultCode>0</resultCode><resultDescription>SUCCESS : You have  topped up  500.00 NGN to 2348113131392.  Your balance is now 262,091.71 NGN.   ref: 2023061017494635404502669</resultDescription><requestedTopupAmount><currency>NGN</currency><value>500</value></requestedTopupAmount><senderPrincipal><principalId><id>WEB8117757318</id><type>RESELLERID</type></principalId><principalName>GLO</principalName><accounts><account><accountDescription>SONITE COMMUNICATIONS LIMITED</accountDescription><accountSpecifier><accountId>WEB8117757318</accountId><accountTypeId>RESELLER</accountTypeId></accountSpecifier><balance><currency>NGN</currency><value>262091.71</value></balance><creditLimit><currency>NGN</currency><value>0.00000</value></creditLimit></account></accounts><status>Active</status><msisdn>2348117757318</msisdn></senderPrincipal><topupAccountSpecifier><accountId>2348113131392</accountId><accountTypeId>AIRTIME</accountTypeId></topupAccountSpecifier><topupAmount><currency>NGN</currency><value>500.00</value></topupAmount><topupPrincipal><principalId><id>2348113131392</id><type>SUBSCRIBERID</type></principalId><principalName></principalName><accounts><account><accountSpecifier><accountId>2348113131392</accountId><accountTypeId>AIRTIME</accountTypeId></accountSpecifier></account><account><accountSpecifier><accountId>2348113131392</accountId><accountTypeId>DATA_BUNDLE</accountTypeId></accountSpecifier></account></accounts></topupPrincipal></return></ns2:requestTopupResponse></soap:Body></soap:Envelope>"""

jsond = xmltodict.parse(resp)
body = jsond["soap:Envelope"]["soap:Body"]["ns2:requestTopupResponse"]["return"]

#print(body["com:errorDescription"])


#print(body)


response = {}
#response["responseCode"] = "90"
response["responseCode"] = body["resultCode"]
response["responseMessage"] = body["resultDescription"]
response["provider_ref"] = body["ersReference"]
response["provider_avail_bal"] = body["senderPrincipal"]["accounts"]["account"]["balance"]["value"]


print(response)
'''

