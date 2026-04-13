from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'staff', views.StaffViewSet, basename='staff')

urlpatterns = [
    path('', include(router.urls)),
    path('health/security/', views.security_health, name='security-health'),
]
