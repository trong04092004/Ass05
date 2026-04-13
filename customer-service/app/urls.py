from django.urls import path
from . import views

urlpatterns = [
    path('health/security/', views.security_health, name='security-health'),

    # Customers CRUD
    path('customers/', views.CustomerListCreate.as_view(), name='customers'),
    path('customers/<int:pk>/', views.CustomerDetail.as_view(), name='customer-detail'),

    # Addresses
    path('customers/<int:customer_id>/addresses/', views.AddressListCreate.as_view(), name='addresses'),
]
