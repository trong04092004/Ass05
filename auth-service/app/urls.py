from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('health/security/', views.security_health, name='security-health'),

    # Auth
    path('auth/customer/register/', views.Register.as_view(), name='customer_register'),
    path('auth/customer/login/', views.Login.as_view(), name='customer_login'),
    path('auth/admin/register/', views.AdminRegister.as_view(), name='admin_register'),
    path('auth/admin/login/', views.AdminLogin.as_view(), name='admin_login'),
    path('auth/logout/', views.logout, name='logout'),

    # Legacy routes (keep backward compatibility)
    path('auth/register/', views.Register.as_view(), name='register'),
    path('auth/login/', views.Login.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
