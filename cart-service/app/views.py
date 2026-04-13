from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings
import hashlib
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from .security import get_customer_id, is_admin


@api_view(['GET'])
@permission_classes([])
def security_health(request):
    signing_key = settings.SIMPLE_JWT.get('SIGNING_KEY', '')
    fingerprint = hashlib.sha256(signing_key.encode()).hexdigest()[:12] if signing_key else ''
    auth_classes = settings.REST_FRAMEWORK.get('DEFAULT_AUTHENTICATION_CLASSES', [])
    return Response({
        'service': 'cart-service',
        'jwt_algorithm': settings.SIMPLE_JWT.get('ALGORITHM', 'HS256'),
        'auth_class': auth_classes[0] if auth_classes else '',
        'jwt_key_fingerprint': fingerprint,
    })


class CartViewSet(viewsets.ModelViewSet):
    """GET /carts/{customer_id}/ → lấy giỏ hàng (trả về list items)"""
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    lookup_field = 'customer_id'
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, customer_id=None):
        if not is_admin(request) and get_customer_id(request) != str(customer_id):
            return Response({'error': 'Forbidden'}, status=403)
        cart, _ = Cart.objects.get_or_create(customer_id=customer_id)
        items = cart.items.all()
        return Response(CartItemSerializer(items, many=True).data)


class CartItemViewSet(viewsets.ModelViewSet):
    """
    POST /cart-items/       → thêm sản phẩm vào giỏ
    PUT  /cart-items/{id}/  → cập nhật số lượng
    DELETE /cart-items/{id}/ → xóa khỏi giỏ
    """
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request):
        customer_id = request.data.get('customer_id')
        book_id = request.data.get('book_id')
        product_service = str(request.data.get('product_service') or '').strip().lower()
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        if book_id and not product_id:
            product_id = book_id
        if book_id and not product_service:
            product_service = 'book'

        if not customer_id or not product_id:
            return Response(
                {'error': 'customer_id và product_id là bắt buộc'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not product_service:
            return Response({'error': 'product_service là bắt buộc'}, status=status.HTTP_400_BAD_REQUEST)

        if not is_admin(request) and get_customer_id(request) != str(customer_id):
            return Response({'error': 'Cannot modify another customer cart'}, status=403)

        cart, _ = Cart.objects.get_or_create(customer_id=customer_id)
        item = CartItem.objects.filter(
            cart=cart,
            product_service=product_service,
            product_id=product_id,
        ).first()
        created = item is None
        if created:
            item = CartItem(
                cart=cart,
                product_service=product_service,
                product_id=product_id,
                book_id=book_id if product_service == 'book' else None,
            )

        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
            if product_service == 'book' and book_id:
                item.book_id = book_id
        item.save()

        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None, *args, **kwargs):
        item = get_object_or_404(CartItem, pk=pk)
        if not is_admin(request) and get_customer_id(request) != str(item.cart.customer_id):
            return Response({'error': 'Forbidden'}, status=403)
        qty = int(request.data.get('quantity', 1))
        if qty <= 0:
            item.delete()
            return Response({'deleted': True})
        item.quantity = qty
        item.save()
        return Response(CartItemSerializer(item).data)

    def destroy(self, request, pk=None):
        item = get_object_or_404(CartItem, pk=pk)
        if not is_admin(request) and get_customer_id(request) != str(item.cart.customer_id):
            return Response({'error': 'Forbidden'}, status=403)
        item.delete()
        return Response({'deleted': True}, status=status.HTTP_204_NO_CONTENT)


@api_view(['DELETE'])
def clear_cart(request, customer_id):
    """DELETE /carts/{customer_id}/clear/ → xóa toàn bộ giỏ"""
    if not request.auth:
        return Response({'error': 'Authentication required'}, status=401)
    if not is_admin(request) and get_customer_id(request) != str(customer_id):
        return Response({'error': 'Forbidden'}, status=403)

    try:
        cart = Cart.objects.get(customer_id=customer_id)
        cart.items.all().delete()
        return Response({'cleared': True})
    except Cart.DoesNotExist:
        return Response({'error': 'Cart not found'}, status=404)