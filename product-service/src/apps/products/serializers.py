from rest_framework import serializers
from .models import Product, Category, Book, Electronics, Fashion, Beauty, Sports, Furniture, Toy, Grocery, Pet, Stationery, Rating


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ('id', 'customer_id', 'product_id', 'rating', 'comment', 'created_at')
        read_only_fields = ('id', 'created_at')


class RatingCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    rating = serializers.IntegerField(required=True, min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True, default='')


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ('author', 'publisher', 'isbn')


class ElectronicsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Electronics
        fields = ('brand', 'warranty')


class FashionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fashion
        fields = ('size', 'color')


class BeautySerializer(serializers.ModelSerializer):
    class Meta:
        model = Beauty
        fields = ('brand', 'volume')


class SportsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sports
        fields = ('brand',)


class FurnitureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Furniture
        fields = ('brand', 'material')


class ToySerializer(serializers.ModelSerializer):
    class Meta:
        model = Toy
        fields = ('brand', 'age_range')


class GrocerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Grocery
        fields = ('brand', 'expiry_date')


class PetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        fields = ('brand', 'pet_type')


class StationerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Stationery
        fields = ('brand',)


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    book = BookSerializer(read_only=True)
    electronics = ElectronicsSerializer(read_only=True)
    fashion = FashionSerializer(read_only=True)
    beauty = BeautySerializer(read_only=True)
    sports = SportsSerializer(read_only=True)
    furniture = FurnitureSerializer(read_only=True)
    toy = ToySerializer(read_only=True)
    grocery = GrocerySerializer(read_only=True)
    pet = PetSerializer(read_only=True)
    stationery = StationerySerializer(read_only=True)
    attributes = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'price', 'category', 'stock', 'attributes', 'images', 'created_at',
                  'book', 'electronics', 'fashion', 'beauty', 'sports', 'furniture', 'toy', 'grocery', 'pet', 'stationery')

    def get_attributes(self, obj):
        attrs = {}
        try:
            if hasattr(obj, 'book') and getattr(obj, 'book') is not None:
                b = obj.book
                attrs.update({'author': b.author, 'publisher': b.publisher, 'isbn': b.isbn})
        except Exception:
            pass
        try:
            if hasattr(obj, 'electronics') and getattr(obj, 'electronics') is not None:
                e = obj.electronics
                attrs.update({'brand': e.brand, 'warranty': e.warranty})
        except Exception:
            pass
        try:
            if hasattr(obj, 'fashion') and getattr(obj, 'fashion') is not None:
                f = obj.fashion
                attrs.update({'size': f.size, 'color': f.color})
        except Exception:
            pass
        try:
            if hasattr(obj, 'beauty') and getattr(obj, 'beauty') is not None:
                bt = obj.beauty
                attrs.update({'brand': bt.brand, 'volume': bt.volume})
        except Exception:
            pass
        try:
            if hasattr(obj, 'sports') and getattr(obj, 'sports') is not None:
                s = obj.sports
                attrs.update({'brand': s.brand})
        except Exception:
            pass
        try:
            if hasattr(obj, 'furniture') and getattr(obj, 'furniture') is not None:
                fu = obj.furniture
                attrs.update({'brand': fu.brand, 'material': fu.material})
        except Exception:
            pass
        try:
            if hasattr(obj, 'toy') and getattr(obj, 'toy') is not None:
                t = obj.toy
                attrs.update({'brand': t.brand, 'age_range': t.age_range})
        except Exception:
            pass
        try:
            if hasattr(obj, 'grocery') and getattr(obj, 'grocery') is not None:
                g = obj.grocery
                attrs.update({'brand': g.brand, 'expiry_date': str(g.expiry_date) if g.expiry_date else None})
        except Exception:
            pass
        try:
            if hasattr(obj, 'pet') and getattr(obj, 'pet') is not None:
                p = obj.pet
                attrs.update({'brand': p.brand, 'pet_type': p.pet_type})
        except Exception:
            pass
        try:
            if hasattr(obj, 'stationery') and getattr(obj, 'stationery') is not None:
                st = obj.stationery
                attrs.update({'brand': st.brand})
        except Exception:
            pass
        return attrs


class ProductCreateSerializer(serializers.ModelSerializer):
    category = serializers.CharField()
    attributes = serializers.JSONField(required=False, write_only=True)
    book = BookSerializer(required=False)
    electronics = ElectronicsSerializer(required=False)
    fashion = FashionSerializer(required=False)
    beauty = BeautySerializer(required=False)
    sports = SportsSerializer(required=False)
    furniture = FurnitureSerializer(required=False)
    toy = ToySerializer(required=False)
    grocery = GrocerySerializer(required=False)
    pet = PetSerializer(required=False)
    stationery = StationerySerializer(required=False)

    class Meta:
        model = Product
        fields = ('name', 'description', 'price', 'category', 'stock', 'attributes', 'images',
                  'book', 'electronics', 'fashion', 'beauty', 'sports', 'furniture', 'toy', 'grocery', 'pet', 'stationery')
        extra_kwargs = {
            'name': {'required': True},
            'price': {'required': True},
        }

    def create(self, validated_data):
        book_data = validated_data.pop('book', None)
        electronics_data = validated_data.pop('electronics', None)
        fashion_data = validated_data.pop('fashion', None)
        beauty_data = validated_data.pop('beauty', None)
        sports_data = validated_data.pop('sports', None)
        furniture_data = validated_data.pop('furniture', None)
        toy_data = validated_data.pop('toy', None)
        grocery_data = validated_data.pop('grocery', None)
        pet_data = validated_data.pop('pet', None)
        stationery_data = validated_data.pop('stationery', None)
        _ = validated_data.pop('attributes', None)
        category_value = validated_data.pop('category', None)

        category = None
        if category_value is None:
            raise serializers.ValidationError({'category': 'This field is required.'})
        try:
            cid = int(category_value)
            category = Category.objects.filter(id=cid).first()
        except Exception:
            category = Category.objects.filter(name__iexact=str(category_value)).first()
        if not category:
            category = Category.objects.create(name=str(category_value))

        validated_data['category'] = category
        product = Product.objects.create(**validated_data)

        if book_data:
            Book.objects.create(product=product, **book_data)
        if electronics_data:
            Electronics.objects.create(product=product, **electronics_data)
        if fashion_data:
            Fashion.objects.create(product=product, **fashion_data)
        if beauty_data:
            Beauty.objects.create(product=product, **beauty_data)
        if sports_data:
            Sports.objects.create(product=product, **sports_data)
        if furniture_data:
            Furniture.objects.create(product=product, **furniture_data)
        if toy_data:
            Toy.objects.create(product=product, **toy_data)
        if grocery_data:
            Grocery.objects.create(product=product, **grocery_data)
        if pet_data:
            Pet.objects.create(product=product, **pet_data)
        if stationery_data:
            Stationery.objects.create(product=product, **stationery_data)

        return product


class ProductUpdateSerializer(serializers.ModelSerializer):
    category = serializers.CharField(required=False)
    attributes = serializers.JSONField(required=False, write_only=True)
    book = BookSerializer(required=False)
    electronics = ElectronicsSerializer(required=False)
    fashion = FashionSerializer(required=False)
    beauty = BeautySerializer(required=False)
    sports = SportsSerializer(required=False)
    furniture = FurnitureSerializer(required=False)
    toy = ToySerializer(required=False)
    grocery = GrocerySerializer(required=False)
    pet = PetSerializer(required=False)
    stationery = StationerySerializer(required=False)

    class Meta:
        model = Product
        fields = ('name', 'description', 'price', 'category', 'stock', 'images',
                  'book', 'electronics', 'fashion', 'beauty', 'sports', 'furniture', 'toy', 'grocery', 'pet', 'stationery')

    def update(self, instance, validated_data):
        category_value = validated_data.pop('category', None)
        _ = validated_data.pop('attributes', None)
        if category_value is not None:
            try:
                cid = int(category_value)
                category = Category.objects.filter(id=cid).first()
            except Exception:
                category = Category.objects.filter(name__iexact=str(category_value)).first()
            if not category:
                category = Category.objects.create(name=str(category_value))
            instance.category = category

        book_data = validated_data.pop('book', None)
        electronics_data = validated_data.pop('electronics', None)
        fashion_data = validated_data.pop('fashion', None)
        beauty_data = validated_data.pop('beauty', None)
        sports_data = validated_data.pop('sports', None)
        furniture_data = validated_data.pop('furniture', None)
        toy_data = validated_data.pop('toy', None)
        grocery_data = validated_data.pop('grocery', None)
        pet_data = validated_data.pop('pet', None)
        stationery_data = validated_data.pop('stationery', None)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        if book_data is not None:
            Book.objects.update_or_create(product=instance, defaults=book_data)
        if electronics_data is not None:
            Electronics.objects.update_or_create(product=instance, defaults=electronics_data)
        if fashion_data is not None:
            Fashion.objects.update_or_create(product=instance, defaults=fashion_data)
        if beauty_data is not None:
            Beauty.objects.update_or_create(product=instance, defaults=beauty_data)
        if sports_data is not None:
            Sports.objects.update_or_create(product=instance, defaults=sports_data)
        if furniture_data is not None:
            Furniture.objects.update_or_create(product=instance, defaults=furniture_data)
        if toy_data is not None:
            Toy.objects.update_or_create(product=instance, defaults=toy_data)
        if grocery_data is not None:
            Grocery.objects.update_or_create(product=instance, defaults=grocery_data)
        if pet_data is not None:
            Pet.objects.update_or_create(product=instance, defaults=pet_data)
        if stationery_data is not None:
            Stationery.objects.update_or_create(product=instance, defaults=stationery_data)

        return instance
