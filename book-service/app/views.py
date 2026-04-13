from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
import hashlib
from .models import Book, BookTag, Collection, CollectionItem
from .serializers import BookSerializer, BookTagSerializer, CollectionSerializer, CollectionItemSerializer
from .security import IsStaffManagerOrReadOnly


@api_view(['GET'])
@permission_classes([AllowAny])
def security_health(request):
    signing_key = settings.SIMPLE_JWT.get('SIGNING_KEY', '')
    fingerprint = hashlib.sha256(signing_key.encode()).hexdigest()[:12] if signing_key else ''
    auth_classes = settings.REST_FRAMEWORK.get('DEFAULT_AUTHENTICATION_CLASSES', [])
    return Response({
        'service': 'book-service',
        'jwt_algorithm': settings.SIMPLE_JWT.get('ALGORITHM', 'HS256'),
        'auth_class': auth_classes[0] if auth_classes else '',
        'jwt_key_fingerprint': fingerprint,
    })

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsStaffManagerOrReadOnly]

class BookTagViewSet(viewsets.ModelViewSet):
    queryset = BookTag.objects.all()
    serializer_class = BookTagSerializer
    permission_classes = [IsStaffManagerOrReadOnly]

class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    permission_classes = [IsStaffManagerOrReadOnly]

class CollectionItemViewSet(viewsets.ModelViewSet):
    queryset = CollectionItem.objects.all()
    serializer_class = CollectionItemSerializer
    permission_classes = [IsStaffManagerOrReadOnly]
