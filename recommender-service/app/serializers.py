from rest_framework import serializers
from .models import ViewHistory
from .models import SearchHistory
from .models import RecommendationCache

class ViewHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewHistory
        fields = '__all__'

class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = '__all__'

class RecommendationCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationCache
        fields = '__all__'

