from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, null=True, blank=True)
    author = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200, null=True, blank=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(default='')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    publication_date = models.DateField(null=True, blank=True)
    isbn = models.CharField(max_length=13, unique=True, null=True, blank=True)
    image_url = models.URLField(blank=True, null=True)
    language = models.CharField(max_length=50, default='Vietnamese')
    format = models.CharField(max_length=50, default='Paperback')  # Hardcover, Ebook, ...
    pages = models.IntegerField(null=True, blank=True)
    avg_rating = models.FloatField(default=0)
    review_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class BookTag(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"#{self.name}"

class Collection(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class CollectionItem(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='collection_items')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('collection', 'book')
