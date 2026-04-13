from django.db import models


class Promotion(models.Model):
    """Chuong trinh khuyen mai - ap dung cho 1 sach hoac tat ca sach."""
    name = models.CharField(max_length=200)
    discount_percent = models.IntegerField(default=0)
    book_id = models.IntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.discount_percent}%)"


class SupplyOrder(models.Model):
    """Phieu nhap hang cho da service san pham."""
    product_service = models.CharField(max_length=32, default='book')
    product_id = models.IntegerField(null=True, blank=True)
    book_id = models.IntegerField(null=True, blank=True)
    quantity = models.IntegerField(default=0)
    supplier = models.CharField(max_length=200, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.product_service == 'book' and self.product_id is None and self.book_id is not None:
            self.product_id = self.book_id
        if self.product_service == 'book' and self.book_id is None and self.product_id is not None:
            self.book_id = self.product_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"SupplyOrder {self.product_service}:{self.product_id} qty={self.quantity}"
