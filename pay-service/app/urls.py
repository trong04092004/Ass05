from django.urls import path
from . import views

urlpatterns = [
    path('payments/', views.PaymentListCreate.as_view(), name='payments'),
    path('payments/order/<int:order_id>/', views.PaymentByOrder.as_view(), name='payment-by-order'),
    path('health/security/', views.security_health, name='security-health'),
]
