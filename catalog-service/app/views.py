from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
import hashlib
from .models import Category
from .models import Author
from .models import Publisher
from .serializers import CategorySerializer, AuthorSerializer, PublisherSerializer
from .security import IsStaffManagerOrReadOnly


@api_view(['GET'])
@permission_classes([AllowAny])
def security_health(request):
    signing_key = settings.SIMPLE_JWT.get('SIGNING_KEY', '')
    fingerprint = hashlib.sha256(signing_key.encode()).hexdigest()[:12] if signing_key else ''
    auth_classes = settings.REST_FRAMEWORK.get('DEFAULT_AUTHENTICATION_CLASSES', [])
    return Response({
        'service': 'catalog-service',
        'jwt_algorithm': settings.SIMPLE_JWT.get('ALGORITHM', 'HS256'),
        'auth_class': auth_classes[0] if auth_classes else '',
        'jwt_key_fingerprint': fingerprint,
    })

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffManagerOrReadOnly]

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsStaffManagerOrReadOnly]

class PublisherViewSet(viewsets.ModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [IsStaffManagerOrReadOnly]

