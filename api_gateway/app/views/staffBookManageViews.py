import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

BOOK_SERVICE_URL = "http://localhost:8001"

@api_view(['GET'])
def book_list(request):
    try:
        r = requests.get(f"{BOOK_SERVICE_URL}/api/books/")
        if r.status_code == 200:
            return Response(r.json())
        return Response({"error": "Failed to fetch books"}, status=r.status_code)
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
