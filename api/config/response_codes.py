"""
Response Codes Definition

Simple list of standardized response codes used across the application.
All codes and messages are based on actual usage in views.py, helper.py, and provider services.
"""

# ============================================================
# SUCCESS CODES (00-09)
# ============================================================
SUCCESS = "00"
"""Transaction or operation completed successfully"""

# ============================================================
# VALIDATION AND INPUT ERROR CODES (00-09)
# ============================================================
TRANSACTION_NOT_FOUND = "01"
"""Transaction not found or does not exist"""

INVALID_PAYLOAD = "02"
"""Invalid request payload, missing required fields, or validation failed"""

NO_DATA_FOUND = "03"
"""No data/records found for the requested query"""

EXCEPTION_ERROR = "04"
"""General exception or unexpected error occurred"""

DAILY_LIMIT_EXCEEDED = "05"
"""Daily transaction limit has been exceeded"""

PROCESSING_ERROR = "06"
"""Unable to process transaction or retrieve data, please try again"""

AUTHENTICATION_ERROR = "07"
"""Authentication failed, invalid token, or unauthorized access"""

INVALID_MSISDN = "08"
"""Invalid phone number (MSISDN) format or number does not exist"""

# ============================================================
# PENDING/PROCESSING CODES (80-89)
# ============================================================
PENDING = "80"
"""Transaction is pending, awaiting response from provider"""

# ============================================================
# ERROR/FAILURE CODES (90-99)
# ============================================================
FAILED = "90"
"""Transaction failed, request failed, or general error occurred"""

NOT_IMPLEMENTED = "99"
"""Feature or functionality not implemented"""

# ============================================================
# RESPONSE CODE MESSAGES MAPPING
# ============================================================
# All messages are based on actual usage in the codebase
RESPONSE_MESSAGES = {
    # Success
    SUCCESS: "Successful",
    
    # Validation and Input Errors
    TRANSACTION_NOT_FOUND: "Transaction not found",
    INVALID_PAYLOAD: "Invalid payload",
    NO_DATA_FOUND: "No data found",
    EXCEPTION_ERROR: "An error occurred",
    DAILY_LIMIT_EXCEEDED: "Your daily transaction limit is exceeded",
    PROCESSING_ERROR: "Unable to process transaction, please try again",
    AUTHENTICATION_ERROR: "Authentication failed",
    INVALID_MSISDN: "Invalid MSISDN",
    
    # Pending
    PENDING: "Transaction is pending, awaiting response from provider",
    
    # Errors
    FAILED: "Request failed",
    NOT_IMPLEMENTED: "Feature not implemented",
}

# ============================================================
# COMMON MESSAGE VARIATIONS (for reference)
# ============================================================
# These are variations of messages used in the codebase that map to the codes above
COMMON_MESSAGES = {
    # Code 00 - Success
    "Successful": SUCCESS,
    "Transaction successful": SUCCESS,
    "Cron job completed successfully": SUCCESS,
    
    # Code 01 - Transaction Not Found
    "Transaction not found": TRANSACTION_NOT_FOUND,
    
    # Code 02 - Invalid Payload
    "Invalid payload": INVALID_PAYLOAD,
    "Invalid request payload": INVALID_PAYLOAD,
    "category_code is required": INVALID_PAYLOAD,
    "product_code is required": INVALID_PAYLOAD,
    "merchant_ref is required": INVALID_PAYLOAD,
    "Amount must be greater than 0": INVALID_PAYLOAD,
    "merchant_ref must contain only alphanumeric characters and hyphens": INVALID_PAYLOAD,
    "Product {product_code} is not active": INVALID_PAYLOAD,
    "This product code {product_code} is not for {category_name}": INVALID_PAYLOAD,
    "Merchant not found": INVALID_PAYLOAD,
    "No route set for sending vend": INVALID_PAYLOAD,
    
    # Code 03 - No Data Found
    "No data found": NO_DATA_FOUND,
    "No products found": NO_DATA_FOUND,
    "No data bundle found": NO_DATA_FOUND,
    "No record found": NO_DATA_FOUND,
    
    # Code 04 - Exception Error
    "An error occurred": EXCEPTION_ERROR,
    
    # Code 05 - Daily Limit Exceeded
    "Your daily transaction limit is exceeded": DAILY_LIMIT_EXCEEDED,
    
    # Code 06 - Processing Error
    "Unable to process transaction, please try again": PROCESSING_ERROR,
    "Unable to retrieve categories, please try again": PROCESSING_ERROR,
    "Unable to retrieve products, please try again": PROCESSING_ERROR,
    "Unable to vend vtu, please try again": PROCESSING_ERROR,
    "Unable to vend data, please try again": PROCESSING_ERROR,
    "Duplicate transaction, please try again": PROCESSING_ERROR,
    
    # Code 07 - Authentication Error
    "Authentication failed": AUTHENTICATION_ERROR,
    "Invalid Token": AUTHENTICATION_ERROR,
    
    # Code 08 - Invalid MSISDN
    "Invalid MSISDN": INVALID_MSISDN,
    
    # Code 80 - Pending
    "Awaiting response from provider": PENDING,
    "Request pending": PENDING,
    "Transaction pending": PENDING,
    "Request timeout after {timeout} seconds": PENDING,
    
    # Code 90 - Failed
    "Request failed": FAILED,
    "Balance check not available for this provider": FAILED,
    
    # Code 99 - Not Implemented
    "Feature not implemented": NOT_IMPLEMENTED,
    "Requery not implemented": NOT_IMPLEMENTED,
    "Balance query not implemented": NOT_IMPLEMENTED,
}

