from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class HandleInvalidRoute(APIView):
    def get(self, request):
        # Custom logic for handling invalid routes or URLs
        return Response({"response": "Not found"}, status=status.HTTP_404_NOT_FOUND)