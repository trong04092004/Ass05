from django.db import models
from django.contrib.auth.models import User

ROLE_CUSTOMER = 'customer'
ROLE_STAFF = 'staff'
ROLE_MANAGER = 'manager'

ROLE_CHOICES = [
    (ROLE_CUSTOMER, 'Khách hàng'),
    (ROLE_STAFF, 'Nhân viên'),
    (ROLE_MANAGER, 'Quản lý'),
]


class Customer(models.Model):
    """
    Domain: Identity - đại diện tài khoản người dùng.
    Liên kết với Django User để tận dụng auth framework.
    role = customer | staff | manager
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='customer_profile', null=True, blank=True
    )
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.role})"


class Address(models.Model):
    """Địa chỉ giao hàng của Customer (nhiều địa chỉ / 1 customer)."""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=50, default='Nhà')
    street = models.CharField(max_length=255)
    ward = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, default='TP. Hồ Chí Minh')
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"[{self.label}] {self.street}, {self.district}, {self.city}"