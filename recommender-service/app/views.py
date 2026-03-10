from rest_framework import viewsets
from .models import ViewHistory
from .models import SearchHistory
from .models import RecommendationCache
from .serializers import ViewHistorySerializer, SearchHistorySerializer, RecommendationCacheSerializer

class ViewHistoryViewSet(viewsets.ModelViewSet):
    queryset = ViewHistory.objects.all()
    serializer_class = ViewHistorySerializer

class SearchHistoryViewSet(viewsets.ModelViewSet):
    queryset = SearchHistory.objects.all()
    serializer_class = SearchHistorySerializer

class RecommendationCacheViewSet(viewsets.ModelViewSet):
    queryset = RecommendationCache.objects.all()
    serializer_class = RecommendationCacheSerializer

