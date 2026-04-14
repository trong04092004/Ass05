from django.db import migrations, models


def backfill_book_sku(apps, schema_editor):
    Book = apps.get_model('app', 'Book')
    used = set(
        sku for sku in Book.objects.exclude(sku__isnull=True).exclude(sku='').values_list('sku', flat=True)
    )

    for book in Book.objects.filter(sku__isnull=True) | Book.objects.filter(sku=''):
        base = (book.isbn or book.slug or f'book-{book.id or ""}'.strip('-') or 'book')[:64]
        candidate = base
        suffix = 1
        while candidate in used:
            trimmed = base[: max(1, 64 - len(str(suffix)) - 1)]
            candidate = f'{trimmed}-{suffix}'
            suffix += 1
        book.sku = candidate
        book.save(update_fields=['sku'])
        used.add(candidate)


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_collection_book_avg_rating_book_format_book_language_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='sku',
            field=models.CharField(blank=True, null=True, default=None, max_length=64),
        ),
        migrations.RunPython(backfill_book_sku, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='book',
            name='sku',
            field=models.CharField(blank=True, default='', max_length=64, unique=True),
        ),
    ]
