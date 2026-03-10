from django.db import models

SHIPPING_STATUS = [
    ('pending', 'Cho giao'),
    ('shipping', 'Dang giao'),
    ('delivered', 'Da giao'),
    ('failed', 'That bai'),
]

SHIPPING_METHOD = [
    ('standard', 'Tieu chuan 3-5 ngay'),
    ('express', 'Nhanh 1-2 ngay'),
]


class Shipping(models.Model):
    """Domain: Shipping - thong tin van chuyen cho 1 don hang."""
    order_id = models.IntegerField(unique=True)
    customer_id = models.IntegerField()
    shipping_method = models.CharField(max_length=20, choices=SHIPPING_METHOD, default='standard')
    address = models.TextField()
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=SHIPPING_STATUS, default='pending')
    tracking_code = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Shipping order={self.order_id} {self.status}"
