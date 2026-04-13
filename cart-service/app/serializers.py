from rest_framework import serializers
from .models import Cart, CartItem

class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'
    product_service = serializers.CharField(required=False, allow_blank=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        service_key = data.get('product_service') or 'book'
        product_id = data.get('product_id')
        if not product_id and data.get('book_id'):
            product_id = data.get('book_id')
        data['product_service'] = service_key
        data['product_id'] = product_id
        return data

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Cart
        fields = '__all__'
