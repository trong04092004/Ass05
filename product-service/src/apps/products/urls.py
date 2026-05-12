from django.urls import path
from .views import (
    HealthView,
    ProductsListCreateView,
    ProductDetailView,
    ProductSearchView,
    ProductSuggestView,
    RatingsListCreateView,
    RatingDetailView,
)

urlpatterns = [
    path('health', HealthView.as_view(), name='health'),
    path('products', ProductsListCreateView.as_view(), name='products-list-create'),
    path('products/<int:id>', ProductDetailView.as_view(), name='product-detail'),
    path('products/search', ProductSearchView.as_view(), name='product-search'),
    path('products/suggest', ProductSuggestView.as_view(), name='product-suggest'),
    # Rating endpoints (replaces comment-service)
    path('ratings', RatingsListCreateView.as_view(), name='ratings-list-create'),
    path('ratings/<int:pk>', RatingDetailView.as_view(), name='rating-detail'),
]
