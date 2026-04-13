"""
Order Service views - Orchestrator dat hang
POST /orders/ se:
  1. Lay items tu Cart Service
  2. Lay gia tung sach tu Book Service
  3. Tao Order + OrderItem trong DB nay
  4. Goi Pay Service -> tao Payment
  5. Goi Ship Service -> tao Shipping
  6. Goi Cart Service -> xoa tung item
"""
import os
import requests
import hashlib
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.conf import settings
from .models import Order, OrderItem
from .serializers import OrderSerializer
from .security import get_customer_id, is_admin

CART_SERVICE_URL = os.environ.get('CART_SERVICE_URL', 'http://localhost:8003')
BOOK_SERVICE_URL = os.environ.get('BOOK_SERVICE_URL', 'http://localhost:8002')
PAY_SERVICE_URL  = os.environ.get('PAY_SERVICE_URL',  'http://localhost:8005')
SHIP_SERVICE_URL = os.environ.get('SHIP_SERVICE_URL', 'http://localhost:8006')
ELECTRONICS_SERVICE_URL = os.environ.get('ELECTRONICS_SERVICE_URL', 'http://localhost:8012')
FASHION_SERVICE_URL = os.environ.get('FASHION_SERVICE_URL', 'http://localhost:8013')
TOY_SERVICE_URL = os.environ.get('TOY_SERVICE_URL', 'http://localhost:8014')
GROCERY_SERVICE_URL = os.environ.get('GROCERY_SERVICE_URL', 'http://localhost:8015')
FURNITURE_SERVICE_URL = os.environ.get('FURNITURE_SERVICE_URL', 'http://localhost:8016')
BEAUTY_SERVICE_URL = os.environ.get('BEAUTY_SERVICE_URL', 'http://localhost:8017')
SPORTS_SERVICE_URL = os.environ.get('SPORTS_SERVICE_URL', 'http://localhost:8018')
PET_SERVICE_URL = os.environ.get('PET_SERVICE_URL', 'http://localhost:8019')
STATIONERY_SERVICE_URL = os.environ.get('STATIONERY_SERVICE_URL', 'http://localhost:8020')

PRODUCT_SERVICE_URLS = {
    'book': BOOK_SERVICE_URL,
    'electronics': ELECTRONICS_SERVICE_URL,
    'fashion': FASHION_SERVICE_URL,
    'toy': TOY_SERVICE_URL,
    'grocery': GROCERY_SERVICE_URL,
    'furniture': FURNITURE_SERVICE_URL,
    'beauty': BEAUTY_SERVICE_URL,
    'sports': SPORTS_SERVICE_URL,
    'pet': PET_SERVICE_URL,
    'stationery': STATIONERY_SERVICE_URL,
}

TIMEOUT = 8


def _auth_headers(request):
    auth = request.META.get('HTTP_AUTHORIZATION') if request else None
    return {'Authorization': auth} if auth else {}


@api_view(['GET'])
@permission_classes([])
def security_health(request):
    signing_key = settings.SIMPLE_JWT.get('SIGNING_KEY', '')
    fingerprint = hashlib.sha256(signing_key.encode()).hexdigest()[:12] if signing_key else ''
    auth_classes = settings.REST_FRAMEWORK.get('DEFAULT_AUTHENTICATION_CLASSES', [])
    return Response({
        'service': 'order-service',
        'jwt_algorithm': settings.SIMPLE_JWT.get('ALGORITHM', 'HS256'),
        'auth_class': auth_classes[0] if auth_classes else '',
        'jwt_key_fingerprint': fingerprint,
    })


def _get(url, headers=None):
    try:
        r = requests.get(url, headers=headers or {}, timeout=TIMEOUT)
        return r.json() if r.ok else None
    except Exception:
        return None


def _post(url, data, headers=None):
    try:
        r = requests.post(url, json=data, headers=headers or {}, timeout=TIMEOUT)
        return r
    except Exception:
        return None


def _delete(url, headers=None):
    try:
        requests.delete(url, headers=headers or {}, timeout=5)
    except Exception:
        pass


class OrderListCreate(APIView):
    """
    GET /orders/  - tat ca don hang (staff/manager)
    POST /orders/ - dat hang moi (orchestration)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_admin(request):
            return Response({'error': 'Staff or manager role required'}, status=403)
        orders = Order.objects.all().order_by('-created_at')
        return Response(OrderSerializer(orders, many=True).data)

    def post(self, request):
        headers = _auth_headers(request)
        customer_id    = request.data.get('customer_id')
        payment_method = request.data.get('payment_method', 'cod')
        shipping_method= request.data.get('shipping_method', 'standard')
        address        = request.data.get('address', '')
        phone          = request.data.get('phone', '')

        if not customer_id:
            return Response({'error': 'customer_id la bat buoc'}, status=400)

        if not is_admin(request) and get_customer_id(request) != str(customer_id):
            return Response({'error': 'Cannot create order for another customer'}, status=403)

        # 1. Lay items tu Cart Service
        cart_items = _get(f"{CART_SERVICE_URL}/carts/{customer_id}/", headers=headers)
        if not cart_items:
            return Response({'error': 'Gio hang trong hoac khong the ket noi cart-service'}, status=400)

        # 2. Lay gia tung sach va tinh total
        total = 0
        enriched = []
        for item in cart_items:
            service_key = (item.get('product_service') or 'book').strip().lower()
            product_id = item.get('product_id') or item.get('book_id')

            service_url = PRODUCT_SERVICE_URLS.get(service_key)
            if not service_url:
                return Response({'error': f'Khong ho tro service: {service_key}'}, status=400)

            endpoint = (
                f"{service_url}/books/{product_id}/"
                if service_key == 'book'
                else f"{service_url}/products/{product_id}/"
            )
            product = _get(endpoint, headers=headers)
            if not product:
                return Response({'error': f'Khong the lay thong tin san pham {service_key}#{product_id}'}, status=400)

            price = float(product.get('price', 0))
            qty   = item.get('quantity', 1)
            total += price * qty
            enriched.append({
                'item_id': item['id'],
                'book_id': item.get('book_id') if service_key == 'book' else None,
                'product_service': service_key,
                'product_id': product_id,
                'quantity': qty,
                'price': price,
            })

        # 3. Tao Order
        order = Order.objects.create(
            customer_id=customer_id,
            total_amount=total,
            payment_method=payment_method,
            shipping_method=shipping_method,
            address=address,
            phone=phone,
            status='pending',
        )
        for ei in enriched:
            OrderItem.objects.create(
                order=order,
                book_id=ei['book_id'],
                product_service=ei['product_service'],
                product_id=ei['product_id'],
                quantity=ei['quantity'],
                price=ei['price'],
            )

        # 4. Goi Pay Service
        _post(f"{PAY_SERVICE_URL}/payments/", {
            'order_id':       order.id,
            'customer_id':    customer_id,
            'amount':         str(total),
            'payment_method': payment_method,
            'status':         'pending',
        }, headers=headers)

        # 5. Goi Ship Service
        _post(f"{SHIP_SERVICE_URL}/shippings/", {
            'order_id':        order.id,
            'customer_id':     customer_id,
            'shipping_method': shipping_method,
            'address':         address,
            'phone':           phone,
            'status':          'pending',
        }, headers=headers)

        # 6. Xoa gio hang sau khi dat hang xong
        for ei in enriched:
            _delete(f"{CART_SERVICE_URL}/cart-items/{ei['item_id']}/", headers=headers)

        return Response(OrderSerializer(order).data, status=201)


class OrderDetail(APIView):
    """GET /orders/<id>/ | PATCH /orders/<id>/ (update status)"""
    permission_classes = [IsAuthenticated]

    def _get_obj(self, pk):
        try:
            return Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return None

    def get(self, request, pk):
        o = self._get_obj(pk)
        if not o:
            return Response({'error': 'Not found'}, status=404)
        if not is_admin(request) and get_customer_id(request) != str(o.customer_id):
            return Response({'error': 'Forbidden'}, status=403)
        return Response(OrderSerializer(o).data)

    def patch(self, request, pk):
        o = self._get_obj(pk)
        if not o:
            return Response({'error': 'Not found'}, status=404)
        if not is_admin(request):
            return Response({'error': 'Staff or manager role required'}, status=403)
        new_status = request.data.get('status')
        if new_status:
            o.status = new_status
            o.save()
        return Response(OrderSerializer(o).data)


class OrderByCustomer(APIView):
    """GET /orders/customer/<customer_id>/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id):
        if not is_admin(request) and get_customer_id(request) != str(customer_id):
            return Response({'error': 'Forbidden'}, status=403)
        orders = Order.objects.filter(customer_id=customer_id).order_by('-created_at')
        return Response(OrderSerializer(orders, many=True).data)
