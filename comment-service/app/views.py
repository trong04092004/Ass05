from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.conf import settings
import hashlib
from .models import Rating
from .serializers import RatingSerializer
from .security import is_customer


@api_view(['GET'])
@permission_classes([AllowAny])
def security_health(request):
    signing_key = settings.SIMPLE_JWT.get('SIGNING_KEY', '')
    fingerprint = hashlib.sha256(signing_key.encode()).hexdigest()[:12] if signing_key else ''
    auth_classes = settings.REST_FRAMEWORK.get('DEFAULT_AUTHENTICATION_CLASSES', [])
    return Response({
        'service': 'comment-service',
        'jwt_algorithm': settings.SIMPLE_JWT.get('ALGORITHM', 'HS256'),
        'auth_class': auth_classes[0] if auth_classes else '',
        'jwt_key_fingerprint': fingerprint,
    })


class RatingListCreate(APIView):
    """POST /ratings/ - tao danh gia | GET /ratings/ - tat ca"""
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Rating.objects.all().order_by('-created_at')
        return Response(RatingSerializer(qs, many=True).data)

    def post(self, request):
        if not is_customer(request):
            return Response({'error': 'Customer login required'}, status=401)

        s = RatingSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


class RatingList(APIView):
    """GET /ratings/list/?book_id=X - danh gia theo sach"""
    permission_classes = [AllowAny]

    def get(self, request):
        book_id = request.query_params.get('book_id')
        qs = Rating.objects.filter(book_id=book_id).order_by('-created_at') if book_id else Rating.objects.none()
        return Response(RatingSerializer(qs, many=True).data)
