from django.db import models


class Rating(models.Model):
    """Domain: Review - danh gia sach sau khi mua."""
    book_id = models.IntegerField()        # FK toi book-service
    customer_id = models.IntegerField()    # FK toi customer-service
    rating = models.IntegerField(default=5)  # 1-5 sao
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating book={self.book_id} by customer={self.customer_id}: {self.rating}*"
