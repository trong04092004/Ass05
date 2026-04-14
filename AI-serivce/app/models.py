from django.db import models
from django.utils import timezone

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


class InteractionEvent(models.Model):
    EVENT_CHOICES = [
        ('view', 'View'),
        ('click', 'Click'),
        ('search', 'Search'),
        ('cart', 'Cart'),
        ('purchase', 'Purchase'),
        ('chat', 'Chat'),
    ]

    customer_id = models.IntegerField(db_index=True)
    session_id = models.CharField(max_length=64, blank=True, default='')
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES, db_index=True)
    product_service = models.CharField(max_length=30, default='book', db_index=True)
    product_id = models.IntegerField(null=True, blank=True, db_index=True)
    category_id = models.IntegerField(null=True, blank=True, db_index=True)
    query = models.CharField(max_length=500, blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    source_service = models.CharField(max_length=50, blank=True, default='api_gateway')
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-occurred_at']

    def __str__(self):
        return f"Event<{self.event_type}> customer={self.customer_id} product={self.product_id}"


class KnowledgeNode(models.Model):
    NODE_CHOICES = [
        ('user', 'User'),
        ('product', 'Product'),
        ('category', 'Category'),
        ('query', 'Query'),
    ]

    node_type = models.CharField(max_length=20, choices=NODE_CHOICES, db_index=True)
    external_id = models.CharField(max_length=255, db_index=True)
    properties = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('node_type', 'external_id')

    def __str__(self):
        return f"{self.node_type}:{self.external_id}"


class KnowledgeEdge(models.Model):
    source = models.ForeignKey(KnowledgeNode, related_name='out_edges', on_delete=models.CASCADE)
    target = models.ForeignKey(KnowledgeNode, related_name='in_edges', on_delete=models.CASCADE)
    relation_type = models.CharField(max_length=50, db_index=True)
    weight = models.FloatField(default=0.0)
    evidence_count = models.IntegerField(default=0)
    last_event_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('source', 'target', 'relation_type')

    def __str__(self):
        return f"{self.source} -[{self.relation_type}:{self.weight:.2f}]-> {self.target}"


class BehaviorModelSnapshot(models.Model):
    model_name = models.CharField(max_length=100, default='markov_v1')
    version = models.CharField(max_length=50, unique=True)
    state_json = models.JSONField(default=dict)
    metrics_json = models.JSONField(default=dict)
    trained_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-trained_at']

    def __str__(self):
        return f"{self.model_name}:{self.version}"


class ActiveModelState(models.Model):
    MODEL_FAMILY_CHOICES = [
        ('behavior', 'Behavior'),
        ('rag', 'RAG'),
    ]

    model_family = models.CharField(max_length=30, choices=MODEL_FAMILY_CHOICES, unique=True)
    active_behavior_snapshot = models.ForeignKey(
        BehaviorModelSnapshot,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='active_states',
    )
    metadata = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"active:{self.model_family}"


class RAGDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ('faq', 'FAQ'),
        ('policy', 'Policy'),
        ('catalog', 'Catalog'),
        ('guide', 'Guide'),
    ]

    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, default='faq', db_index=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    token_count = models.IntegerField(default=0)
    embedding_hint = models.JSONField(default=list, blank=True)
    embedding = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.doc_type}:{self.title}"
