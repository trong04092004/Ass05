from django.contrib import admin
from .models import Product, Category, Book, Electronics, Fashion, Beauty, Sports, Furniture, Toy, Grocery, Pet, Stationery


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'get_category', 'price', 'stock', 'created_at')
    search_fields = ('name', 'description')

    def get_category(self, obj):
        return obj.category.name if obj.category else ''
    get_category.short_description = 'Category'


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'author', 'publisher', 'isbn')


@admin.register(Electronics)
class ElectronicsAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'brand', 'warranty')


@admin.register(Fashion)
class FashionAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'size', 'color')


@admin.register(Beauty)
class BeautyAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'brand', 'volume')


@admin.register(Sports)
class SportsAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'brand')


@admin.register(Furniture)
class FurnitureAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'brand', 'material')


@admin.register(Toy)
class ToyAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'brand', 'age_range')


@admin.register(Grocery)
class GroceryAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'brand', 'expiry_date')


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'brand', 'pet_type')


@admin.register(Stationery)
class StationeryAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'brand')
