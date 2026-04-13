from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from app import views as v
import os


FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

urlpatterns = [
    path('admin/', admin.site.urls),

    # New frontend entrypoint (React app)
    path('', RedirectView.as_view(url=FRONTEND_URL, permanent=False), name='frontend-home'),

    # === API Proxy (JSON) ===
    path('api/books/',          v.api_books,        name='api_books'),
    path('api/books/<int:pk>/', v.api_book_detail,  name='api_book_detail'),
    path('api/auth/register/',  v.api_auth_register, name='api_auth_register'),
    path('api/auth/login/',     v.api_auth_login,   name='api_auth_login'),
    path('api/auth/admin/register/', v.api_auth_admin_register, name='api_auth_admin_register'),
    path('api/auth/admin/login/',    v.api_auth_admin_login,    name='api_auth_admin_login'),
    path('api/auth/refresh/',   v.api_auth_refresh, name='api_auth_refresh'),
    path('api/auth/logout/',    v.api_auth_logout,  name='api_auth_logout'),
    path('api/customers/',      v.api_customers,    name='api_customers'),
    path('api/customers/<int:pk>/', v.api_customer_detail, name='api_customer_detail'),
    path('api/customers/<int:customer_id>/addresses/', v.api_customer_addresses, name='api_customer_addresses'),
    path('api/cart/<int:customer_id>/', v.api_cart, name='api_cart'),
    path('api/cart-items/',     v.api_cart_items,   name='api_cart_items'),
    path('api/cart-items/<int:pk>/', v.api_cart_item_detail, name='api_cart_item_detail'),
    path('api/orders/',         v.api_orders,       name='api_orders'),
    path('api/orders/<int:pk>/', v.api_order_detail, name='api_order_detail'),
    path('api/orders/customer/<int:customer_id>/', v.api_orders_by_customer, name='api_orders_by_customer'),
    path('api/ratings/',        v.api_ratings,      name='api_ratings'),
    path('api/ratings/list/',   v.api_ratings_list, name='api_ratings_list'),
    path('api/promotions/',     v.api_promotions,   name='api_promotions'),
    path('api/supply-orders/',  v.api_supply_orders, name='api_supply_orders'),
    path('api/staff/',          v.api_staff, name='api_staff'),
    path('api/categories/',     v.api_categories, name='api_categories'),
    path('api/categories/<int:pk>/', v.api_category_detail, name='api_category_detail'),
    path('api/products/<str:service_key>/', v.api_product_catalog, name='api_product_catalog'),
    path('api/products/<str:service_key>/<int:pk>/', v.api_product_detail, name='api_product_detail'),

    # Swagger
    path('api/schema/',  SpectacularAPIView.as_view(),                         name='schema'),
    path('api/docs/',    SpectacularSwaggerView.as_view(url_name='schema'),    name='swagger-ui'),
]
