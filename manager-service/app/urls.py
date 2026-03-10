from django.urls import path
from . import views

urlpatterns = [
    path('promotions/', views.PromotionListCreate.as_view(), name='promotions'),
    path('supply-orders/', views.SupplyOrderListCreate.as_view(), name='supply-orders'),
]
