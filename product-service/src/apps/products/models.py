from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Rating(models.Model):
    """Rating for products - replaces comment-service ratings."""
    customer_id = models.IntegerField(db_index=True)
    product_id = models.IntegerField(db_index=True)
    rating = models.IntegerField(default=5, choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'ratings'
        unique_together = ('customer_id', 'product_id')

    def __str__(self):
        return f"Rating {self.rating}/5 for product {self.product_id} by customer {self.customer_id}"


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    stock = models.IntegerField(default=0)
    images = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.category.name if self.category else 'uncategorized'})"


class Book(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='book')
    author = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255)
    isbn = models.CharField(max_length=20)

    def __str__(self):
        return f"Book({self.product.name})"


class Electronics(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='electronics')
    brand = models.CharField(max_length=100)
    warranty = models.IntegerField()

    def __str__(self):
        return f"Electronics({self.product.name})"


class Fashion(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='fashion')
    size = models.CharField(max_length=10)
    color = models.CharField(max_length=50)

    def __str__(self):
        return f"Fashion({self.product.name})"


class Beauty(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='beauty')
    brand = models.CharField(max_length=100)
    volume = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Beauty({self.product.name})"


class Sports(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='sports')
    brand = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f"Sports({self.product.name})"


class Furniture(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='furniture')
    brand = models.CharField(max_length=120, blank=True)
    material = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Furniture({self.product.name})"


class Toy(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='toy')
    brand = models.CharField(max_length=120, blank=True)
    age_range = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Toy({self.product.name})"


class Grocery(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='grocery')
    brand = models.CharField(max_length=120, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Grocery({self.product.name})"


class Pet(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='pet')
    brand = models.CharField(max_length=120, blank=True)
    pet_type = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Pet({self.product.name})"


class Stationery(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='stationery')
    brand = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f"Stationery({self.product.name})"
