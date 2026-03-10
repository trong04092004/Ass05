from rest_framework import viewsets
from .models import Book, BookTag, Collection, CollectionItem
from .serializers import BookSerializer, BookTagSerializer, CollectionSerializer, CollectionItemSerializer

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

class BookTagViewSet(viewsets.ModelViewSet):
    queryset = BookTag.objects.all()
    serializer_class = BookTagSerializer

class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer

class CollectionItemViewSet(viewsets.ModelViewSet):
    queryset = CollectionItem.objects.all()
    serializer_class = CollectionItemSerializer
