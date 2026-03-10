from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.Register.as_view(), name='register'),
    path('auth/login/', views.Login.as_view(), name='login'),

    # Customers CRUD
    path('customers/', views.CustomerListCreate.as_view(), name='customers'),
    path('customers/<int:pk>/', views.CustomerDetail.as_view(), name='customer-detail'),

    # Addresses
    path('customers/<int:customer_id>/addresses/', views.AddressListCreate.as_view(), name='addresses'),
]
