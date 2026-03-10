from rest_framework import serializers
from .models import Book, BookTag, Collection, CollectionItem


class BookTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookTag
        fields = '__all__'


class CollectionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionItem
        fields = '__all__'


class CollectionSerializer(serializers.ModelSerializer):
    items = CollectionItemSerializer(many=True, read_only=True)

    class Meta:
        model = Collection
        fields = '__all__'


class BookSerializer(serializers.ModelSerializer):
    tags = BookTagSerializer(many=True, read_only=True)
    # Alias 'stock' -> 'stock_quantity' de dong bo voi API Gateway va cac service khac
    stock = serializers.IntegerField(source='stock_quantity', default=0)

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'slug', 'author', 'publisher', 'category',
            'description', 'price', 'stock', 'stock_quantity',
            'publication_date', 'isbn', 'image_url', 'language', 'format',
            'pages', 'avg_rating', 'review_count', 'created_at', 'updated_at',
            'tags',
        ]
