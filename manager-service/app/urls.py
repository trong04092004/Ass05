from django.urls import path
from . import views

urlpatterns = [
    path('promotions/', views.PromotionListCreate.as_view(), name='promotions'),
    path('supply-orders/', views.SupplyOrderListCreate.as_view(), name='supply-orders'),
    path('health/security/', views.security_health, name='security-health'),
]
