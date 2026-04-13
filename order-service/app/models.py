from django.db import models

ORDER_STATUS = [
    ('pending', 'Cho xu ly'),
    ('confirmed', 'Da xac nhan'),
    ('shipping', 'Dang giao'),
    ('completed', 'Hoan thanh'),
    ('cancelled', 'Da huy'),
]


class Order(models.Model):
    """Domain: Ordering - don hang cua khach hang."""
    customer_id = models.IntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, default='cod')
    shipping_method = models.CharField(max_length=20, default='standard')
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} customer={self.customer_id} {self.status}"


class OrderItem(models.Model):
    """Cac san pham trong 1 don hang."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    # Legacy field for old clients and backward compatibility.
    book_id = models.IntegerField(null=True, blank=True)
    # Generic product reference.
    product_service = models.CharField(max_length=40, default='book')
    product_id = models.IntegerField(null=True, blank=True)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Gia tai thoi diem dat

    def __str__(self):
        return f"OrderItem order={self.order_id} {self.product_service}:{self.product_id} x{self.quantity}"
