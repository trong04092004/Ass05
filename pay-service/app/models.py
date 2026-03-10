from django.db import models


PAYMENT_STATUS = [
    ('pending', 'Cho xu ly'),
    ('completed', 'Da thanh toan'),
    ('failed', 'That bai'),
    ('refunded', 'Hoan tien'),
]

PAYMENT_METHOD = [
    ('cod', 'COD - Thu tien khi giao'),
    ('bank', 'Chuyen khoan ngan hang'),
    ('card', 'The tin dung / ghi no'),
]


class Payment(models.Model):
    """Domain: Payment - giao dich thanh toan cho 1 don hang."""
    order_id = models.IntegerField(unique=True)      # FK toi order-service
    customer_id = models.IntegerField()              # FK toi customer-service
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD, default='cod')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment order={self.order_id} amount={self.amount} {self.status}"
