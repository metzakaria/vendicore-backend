#merchant api views
from rest_framework.permissions import AllowAny
from apps.merchant.models import Merchant
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.response import Response
import logging
logger = logging.getLogger(__name__)

class MerchantApiView(viewsets.ViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def list(self, request):
        return Response({"message": "Hello, world!"})