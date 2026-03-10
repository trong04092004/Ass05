from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer


class CartViewSet(viewsets.ModelViewSet):
    """GET /carts/{customer_id}/ → lấy giỏ hàng (trả về list items)"""
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    lookup_field = 'customer_id'

    def retrieve(self, request, customer_id=None):
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

    def create(self, request):
        customer_id = request.data.get('customer_id')
        book_id = request.data.get('book_id')
        quantity = int(request.data.get('quantity', 1))

        if not customer_id or not book_id:
            return Response(
                {'error': 'customer_id và book_id là bắt buộc'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart, _ = Cart.objects.get_or_create(customer_id=customer_id)
        item, created = CartItem.objects.get_or_create(
            cart=cart, book_id=book_id
        )
        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        item.save()

        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        item = get_object_or_404(CartItem, pk=pk)
        qty = int(request.data.get('quantity', 1))
        if qty <= 0:
            item.delete()
            return Response({'deleted': True})
        item.quantity = qty
        item.save()
        return Response(CartItemSerializer(item).data)

    def destroy(self, request, pk=None):
        item = get_object_or_404(CartItem, pk=pk)
        item.delete()
        return Response({'deleted': True}, status=status.HTTP_204_NO_CONTENT)


@api_view(['DELETE'])
def clear_cart(request, customer_id):
    """DELETE /carts/{customer_id}/clear/ → xóa toàn bộ giỏ"""
    try:
        cart = Cart.objects.get(customer_id=customer_id)
        cart.items.all().delete()
        return Response({'cleared': True})
    except Cart.DoesNotExist:
        return Response({'error': 'Cart not found'}, status=404)