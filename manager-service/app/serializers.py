from rest_framework import serializers
from .models import Promotion, SupplyOrder

class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = '__all__'
        read_only_fields = ['created_at']

class SupplyOrderSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        service = attrs.get('product_service') or 'book'
        product_id = attrs.get('product_id')
        book_id = attrs.get('book_id')

        if service == 'book':
            if product_id is None and book_id is None:
                raise serializers.ValidationError({'product_id': 'product_id hoac book_id la bat buoc voi service=book.'})
            if product_id is None:
                attrs['product_id'] = book_id
            if book_id is None:
                attrs['book_id'] = product_id
        else:
            if product_id is None and book_id is not None:
                attrs['product_id'] = book_id
            if attrs.get('product_id') is None:
                raise serializers.ValidationError({'product_id': 'product_id la bat buoc voi service khac book.'})

        attrs['product_service'] = service
        return attrs

    class Meta:
        model = SupplyOrder
        fields = '__all__'
        read_only_fields = ['created_at']
