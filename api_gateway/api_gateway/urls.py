from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from app import views as v

urlpatterns = [
    path('admin/', admin.site.urls),

    # === SSR Pages ===
    path('', v.home, name='home'),
    path('auth/register/', v.register_page, name='register_page'),
    path('auth/login/',    v.login_page,    name='login_page'),
    path('auth/logout/',   v.logout_view,   name='logout'),

    # Books
    path('books/',                  v.book_list,   name='book_list'),
    path('books/<int:book_id>/',    v.book_detail, name='book_detail'),
    path('books/<int:book_id>/rate/', v.rate_book, name='rate_book'),

    # Cart
    path('my-cart/',                        v.my_cart,          name='my_cart'),
    path('add-to-cart/<int:book_id>/',      v.add_to_cart,      name='add_to_cart'),
    path('remove-cart-item/<int:item_id>/', v.remove_cart_item, name='remove_cart_item'),
    path('update-cart-item/<int:item_id>/', v.update_cart_item, name='update_cart_item'),

    # Checkout & Orders
    path('checkout/',    v.checkout,     name='checkout'),
    path('place-order/', v.place_order,  name='place_order'),
    path('orders/',      v.order_history, name='order_history'),

    # Profile
    path('profile/', v.profile, name='profile'),

    # Staff
    path('staff/',                              v.staff_books,  name='staff_books'),
    path('staff/books/edit/<int:book_id>/',     v.staff_edit_book, name='staff_edit_book'),
    path('staff/orders/',                       v.staff_orders, name='staff_orders'),
    path('staff/orders/<int:order_id>/status/', v.staff_update_order_status, name='staff_update_order_status'),
    path('staff/inventory/',                    v.manager_inventory, name='staff_inventory'),

    # Manager
    path('manager/',                                    v.manager_dashboard,        name='manager_dashboard'),
    path('manager/promotions/',                         v.manager_promotions,       name='manager_promotions'),
    path('manager/inventory/',                          v.manager_inventory,        name='manager_inventory'),
    path('manager/categories/',                         v.manager_categories,       name='manager_categories'),
    path('manager/categories/<int:category_id>/update/', v.manager_categories_update, name='manager_categories_update'),

    # === API Proxy (JSON) ===
    path('api/books/',          v.api_books,        name='api_books'),
    path('api/books/<int:pk>/', v.api_book_detail,  name='api_book_detail'),
    path('api/auth/register/',  v.api_auth_register, name='api_auth_register'),
    path('api/auth/login/',     v.api_auth_login,   name='api_auth_login'),
    path('api/customers/',      v.api_customers,    name='api_customers'),
    path('api/cart/<int:customer_id>/', v.api_cart, name='api_cart'),
    path('api/cart-items/',     v.api_cart_items,   name='api_cart_items'),
    path('api/cart-items/<int:pk>/', v.api_cart_item_detail, name='api_cart_item_detail'),
    path('api/orders/',         v.api_orders,       name='api_orders'),
    path('api/ratings/',        v.api_ratings,      name='api_ratings'),
    path('api/ratings/list/',   v.api_ratings_list, name='api_ratings_list'),
    path('api/promotions/',     v.api_promotions,   name='api_promotions'),

    # Swagger
    path('api/schema/',  SpectacularAPIView.as_view(),                         name='schema'),
    path('api/docs/',    SpectacularSwaggerView.as_view(url_name='schema'),    name='swagger-ui'),
]
