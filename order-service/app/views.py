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
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order, OrderItem
from .serializers import OrderSerializer

CART_SERVICE_URL = os.environ.get('CART_SERVICE_URL', 'http://localhost:8003')
BOOK_SERVICE_URL = os.environ.get('BOOK_SERVICE_URL', 'http://localhost:8002')
PAY_SERVICE_URL  = os.environ.get('PAY_SERVICE_URL',  'http://localhost:8005')
SHIP_SERVICE_URL = os.environ.get('SHIP_SERVICE_URL', 'http://localhost:8006')

TIMEOUT = 8


def _get(url):
    try:
        r = requests.get(url, timeout=TIMEOUT)
        return r.json() if r.ok else None
    except Exception:
        return None


def _post(url, data):
    try:
        r = requests.post(url, json=data, timeout=TIMEOUT)
        return r
    except Exception:
        return None


def _delete(url):
    try:
        requests.delete(url, timeout=5)
    except Exception:
        pass


class OrderListCreate(APIView):
    """
    GET /orders/  - tat ca don hang (staff/manager)
    POST /orders/ - dat hang moi (orchestration)
    """
    def get(self, request):
        orders = Order.objects.all().order_by('-created_at')
        return Response(OrderSerializer(orders, many=True).data)

    def post(self, request):
        customer_id    = request.data.get('customer_id')
        payment_method = request.data.get('payment_method', 'cod')
        shipping_method= request.data.get('shipping_method', 'standard')
        address        = request.data.get('address', '')
        phone          = request.data.get('phone', '')

        if not customer_id:
            return Response({'error': 'customer_id la bat buoc'}, status=400)

        # 1. Lay items tu Cart Service
        cart_items = _get(f"{CART_SERVICE_URL}/carts/{customer_id}/")
        if not cart_items:
            return Response({'error': 'Gio hang trong hoac khong the ket noi cart-service'}, status=400)

        # 2. Lay gia tung sach va tinh total
        total = 0
        enriched = []
        for item in cart_items:
            book = _get(f"{BOOK_SERVICE_URL}/books/{item['book_id']}/")
            if not book:
                return Response({'error': f'Khong the lay thong tin sach #{item["book_id"]}'}, status=400)
            price = float(book.get('price', 0))
            qty   = item.get('quantity', 1)
            total += price * qty
            enriched.append({'item_id': item['id'], 'book_id': item['book_id'], 'quantity': qty, 'price': price})

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
            OrderItem.objects.create(order=order, book_id=ei['book_id'], quantity=ei['quantity'], price=ei['price'])

        # 4. Goi Pay Service
        _post(f"{PAY_SERVICE_URL}/payments/", {
            'order_id':       order.id,
            'customer_id':    customer_id,
            'amount':         str(total),
            'payment_method': payment_method,
            'status':         'pending',
        })

        # 5. Goi Ship Service
        _post(f"{SHIP_SERVICE_URL}/shippings/", {
            'order_id':        order.id,
            'customer_id':     customer_id,
            'shipping_method': shipping_method,
            'address':         address,
            'phone':           phone,
            'status':          'pending',
        })

        # 6. Xoa gio hang sau khi dat hang xong
        for ei in enriched:
            _delete(f"{CART_SERVICE_URL}/cart-items/{ei['item_id']}/")

        return Response(OrderSerializer(order).data, status=201)


class OrderDetail(APIView):
    """GET /orders/<id>/ | PATCH /orders/<id>/ (update status)"""
    def _get_obj(self, pk):
        try:
            return Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return None

    def get(self, request, pk):
        o = self._get_obj(pk)
        return Response(OrderSerializer(o).data) if o else Response({'error': 'Not found'}, status=404)

    def patch(self, request, pk):
        o = self._get_obj(pk)
        if not o:
            return Response({'error': 'Not found'}, status=404)
        new_status = request.data.get('status')
        if new_status:
            o.status = new_status
            o.save()
        return Response(OrderSerializer(o).data)


class OrderByCustomer(APIView):
    """GET /orders/customer/<customer_id>/"""
    def get(self, request, customer_id):
        orders = Order.objects.filter(customer_id=customer_id).order_by('-created_at')
        return Response(OrderSerializer(orders, many=True).data)
