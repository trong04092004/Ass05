from django.db import models

class Cart(models.Model):
    customer_id = models.IntegerField(unique=True) # Liên kết gián tiếp sang customer-service
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    # Legacy field for book-service compatibility.
    book_id = models.IntegerField(null=True, blank=True)
    # Generic product reference across all services.
    product_service = models.CharField(max_length=40, default='book')
    product_id = models.IntegerField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)