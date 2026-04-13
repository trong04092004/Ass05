from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.conf import settings
import hashlib
from .models import Shipping
from .serializers import ShippingSerializer
from .security import get_customer_id, get_role


@api_view(['GET'])
@permission_classes([])
def security_health(request):
    signing_key = settings.SIMPLE_JWT.get('SIGNING_KEY', '')
    fingerprint = hashlib.sha256(signing_key.encode()).hexdigest()[:12] if signing_key else ''
    auth_classes = settings.REST_FRAMEWORK.get('DEFAULT_AUTHENTICATION_CLASSES', [])
    return Response({
        'service': 'ship-service',
        'jwt_algorithm': settings.SIMPLE_JWT.get('ALGORITHM', 'HS256'),
        'auth_class': auth_classes[0] if auth_classes else '',
        'jwt_key_fingerprint': fingerprint,
    })


class ShippingListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if get_role(request) not in ('staff', 'manager'):
            return Response({'error': 'Staff or manager role required'}, status=403)
        return Response(ShippingSerializer(Shipping.objects.all().order_by('-created_at'), many=True).data)

    def post(self, request):
        role = get_role(request)
        req_customer_id = get_customer_id(request)
        payload_customer_id = str(request.data.get('customer_id')) if request.data.get('customer_id') is not None else None
        if role not in ('customer', 'staff', 'manager'):
            return Response({'error': 'Authentication required'}, status=401)
        if role == 'customer' and req_customer_id != payload_customer_id:
            return Response({'error': 'Cannot create shipping for another customer'}, status=403)

        s = ShippingSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=201)
        return Response(s.errors, status=400)

class ShippingByOrder(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            shipping = Shipping.objects.get(order_id=order_id)
            role = get_role(request)
            req_customer_id = get_customer_id(request)
            if role not in ('staff', 'manager') and str(shipping.customer_id) != req_customer_id:
                return Response({'error': 'Forbidden'}, status=403)
            return Response(ShippingSerializer(shipping).data)
        except Shipping.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
