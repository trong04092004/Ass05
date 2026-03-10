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
    """Phieu nhap hang cho book-service."""
    book_id = models.IntegerField()
    quantity = models.IntegerField(default=0)
    supplier = models.CharField(max_length=200, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SupplyOrder book={self.book_id} qty={self.quantity}"
