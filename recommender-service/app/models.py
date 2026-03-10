from django.db import models

class ViewHistory(models.Model):
    """Theo dõi lịch sử xem sách của khách hàng."""
    customer_id = models.IntegerField()
    book_id = models.IntegerField()
    viewed_at = models.DateTimeField(auto_now_add=True)
    view_duration_secs = models.IntegerField(default=0)

    def __str__(self):
        return f"Customer#{self.customer_id} viewed Book#{self.book_id}"

class SearchHistory(models.Model):
    customer_id = models.IntegerField()
    query = models.CharField(max_length=255)
    searched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Customer#{self.customer_id}: \"{self.query}\""

class RecommendationCache(models.Model):
    """Lưu cache gợi ý đã tính toán để trả về nhanh."""
    customer_id = models.IntegerField(unique=True)
    recommended_book_ids = models.JSONField(default=list)
    reason = models.CharField(max_length=100, default='collaborative_filtering')
    generated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Recommendations for Customer#{self.customer_id}"
