import requests
import hashlib
import time
import random
import base64
import bcrypt
from datetime import datetime
#creditswitch connection


url = "http://176.58.99.160:9014/api/v1/mvend"
url = "http://sandbox.creditswitch.net:9014/api/v1/mvend"

#url = "https://portal.creditswitch.com/api/v1/mvend"

loginId = "315507"
Password = "1@r2yu%GR7H_"
publicKey = "Jl7MMMQxPI4yz9Ch0dE7xYunhog7smyJaj49gGOxotkFcQhMVRX81OmZarznjuNBxto7c8"
privateKey = "oacF4J9UbU6Am09AoXNcUfCBE0z13w2h4RO0nkZ0IIin6j9fEkBeBYWzr6I0ClCKNhg8zW"

#loginId = "3733757"
#publicKey = "YlteOlCVU05XBMhOkw5AmOUu3aIFUXTw6eabIv7FY3M8tWGOhNAIx42duG5oFpuOoAppeA"
#privateKey = "yji35oMRUrWUSp4sz0AQIEjgZxCg8JYUTeYEHdekAaUjkQ33xtKPgeFmNIdYGammo4UWaq"


requestId = str(random.randint(1000000, 9999999))
serviceId = "A04E"
requestAmount = "100"
recipient = "08069335817"

concatString = f"{loginId}|{requestId}|{serviceId}|{requestAmount}|{privateKey}|{recipient}"
concatBytes = concatString.encode("utf-8")[:72]

salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(concatBytes, salt)
checksum = base64.b64encode(hashed).decode("utf-8")

#sha256_hash = hashlib.sha256(concatBytes).digest()
#checksum = base64.b64encode(sha256_hash).decode("utf-8")
print(checksum)
#checksum

payload = {
    "loginId": loginId,
    "key": publicKey,
    "requestId": requestId,
    "serviceId": serviceId,
    "amount": requestAmount,
    "recipient": recipient,
    "date": str(datetime.now()),
    "checksum": checksum
}

start_time = time.time() 
resp = requests.post(url,json=payload).content 
end_time = time.time() 

response_time = end_time - start_time
print(f"RESPONSE TIME: {response_time} seconds")


print(resp)