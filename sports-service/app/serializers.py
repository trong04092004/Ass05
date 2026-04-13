from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    stock = serializers.IntegerField(source='stock_quantity', default=0)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'brand', 'description', 'price',
            'stock', 'stock_quantity', 'image_url', 'created_at', 'updated_at'
        ]