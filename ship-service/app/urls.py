from django.urls import path
from . import views

urlpatterns = [
    path('shippings/', views.ShippingListCreate.as_view(), name='shippings'),
    path('shippings/order/<int:order_id>/', views.ShippingByOrder.as_view(), name='shipping-by-order'),
    path('health/security/', views.security_health, name='security-health'),
]
