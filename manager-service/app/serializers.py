from rest_framework import serializers
from .models import Promotion, SupplyOrder

class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = '__all__'
        read_only_fields = ['created_at']

class SupplyOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplyOrder
        fields = '__all__'
        read_only_fields = ['created_at']
