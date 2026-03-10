from django.db import models

class Cart(models.Model):
    customer_id = models.IntegerField(unique=True) # Liên kết gián tiếp sang customer-service
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    book_id = models.IntegerField() # Liên kết gián tiếp sang book-service
    quantity = models.PositiveIntegerField(default=1)