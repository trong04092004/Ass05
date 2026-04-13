from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartitem',
            name='book_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='product_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='product_service',
            field=models.CharField(default='book', max_length=40),
        ),
        migrations.RunSQL(
            sql="""
                UPDATE app_cartitem
                SET product_service = 'book', product_id = book_id
                WHERE (product_id IS NULL OR product_service = '') AND book_id IS NOT NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
