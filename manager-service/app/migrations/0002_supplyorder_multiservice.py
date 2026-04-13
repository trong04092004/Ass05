from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplyorder',
            name='product_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='supplyorder',
            name='product_service',
            field=models.CharField(default='book', max_length=32),
        ),
        migrations.AlterField(
            model_name='supplyorder',
            name='book_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.RunSQL(
            "UPDATE app_supplyorder SET product_id = book_id WHERE product_id IS NULL AND book_id IS NOT NULL;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
