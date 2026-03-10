from django.db import models
from django.contrib.auth.models import User

class Staff(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('MANAGER', 'Manager'),
        ('STAFF', 'Staff'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='STAFF')
    employee_code = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} [{self.role}]"

class StaffPermission(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='permissions')
    resource = models.CharField(max_length=100)  # e.g. 'books', 'orders'
    can_create = models.BooleanField(default=False)
    can_read = models.BooleanField(default=True)
    can_update = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    class Meta:
        unique_together = ('staff', 'resource')

    def __str__(self):
        return f"{self.staff} -> {self.resource}"
