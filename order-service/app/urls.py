from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.OrderListCreate.as_view(), name='orders'),
    path('orders/<int:pk>/', views.OrderDetail.as_view(), name='order-detail'),
    path('orders/customer/<int:customer_id>/', views.OrderByCustomer.as_view(), name='order-by-customer'),
]
