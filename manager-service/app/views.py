from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.conf import settings
import hashlib
from .models import Promotion, SupplyOrder
from .serializers import PromotionSerializer, SupplyOrderSerializer
from .security import get_role


@api_view(['GET'])
@permission_classes([AllowAny])
def security_health(request):
    signing_key = settings.SIMPLE_JWT.get('SIGNING_KEY', '')
    fingerprint = hashlib.sha256(signing_key.encode()).hexdigest()[:12] if signing_key else ''
    auth_classes = settings.REST_FRAMEWORK.get('DEFAULT_AUTHENTICATION_CLASSES', [])
    return Response({
        'service': 'manager-service',
        'jwt_algorithm': settings.SIMPLE_JWT.get('ALGORITHM', 'HS256'),
        'auth_class': auth_classes[0] if auth_classes else '',
        'jwt_key_fingerprint': fingerprint,
    })


class PromotionListCreate(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(PromotionSerializer(Promotion.objects.all().order_by('-created_at'), many=True).data)

    def post(self, request):
        if get_role(request) != 'manager':
            return Response({'error': 'Manager role required'}, status=403)
        s = PromotionSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


class SupplyOrderListCreate(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if get_role(request) not in ('staff', 'manager'):
            return Response({'error': 'Staff or manager role required'}, status=403)
        return Response(SupplyOrderSerializer(SupplyOrder.objects.all().order_by('-created_at'), many=True).data)

    def post(self, request):
        if get_role(request) not in ('staff', 'manager'):
            return Response({'error': 'Staff or manager role required'}, status=403)
        s = SupplyOrderSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=201)
        return Response(s.errors, status=400)
