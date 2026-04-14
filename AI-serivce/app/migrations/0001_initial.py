# Generated manually for AI service initial schema.

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.RunSQL(
            sql=(
                """
                DO $$
                BEGIN
                    CREATE EXTENSION IF NOT EXISTS vector;
                EXCEPTION
                    WHEN undefined_file OR feature_not_supported THEN
                        RAISE NOTICE 'pgvector extension is not installed on this PostgreSQL instance; continuing without extension';
                END
                $$;
                """
            ),
            reverse_sql="DROP EXTENSION IF EXISTS vector;",
        ),
        migrations.CreateModel(
            name='BehaviorModelSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model_name', models.CharField(default='markov_v1', max_length=100)),
                ('version', models.CharField(max_length=50, unique=True)),
                ('state_json', models.JSONField(default=dict)),
                ('metrics_json', models.JSONField(default=dict)),
                ('trained_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-trained_at'],
            },
        ),
        migrations.CreateModel(
            name='InteractionEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_id', models.IntegerField(db_index=True)),
                ('session_id', models.CharField(blank=True, default='', max_length=64)),
                ('event_type', models.CharField(choices=[('view', 'View'), ('click', 'Click'), ('search', 'Search'), ('cart', 'Cart'), ('purchase', 'Purchase'), ('chat', 'Chat')], db_index=True, max_length=20)),
                ('product_service', models.CharField(db_index=True, default='book', max_length=30)),
                ('product_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('category_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('query', models.CharField(blank=True, default='', max_length=500)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('source_service', models.CharField(blank=True, default='api_gateway', max_length=50)),
                ('occurred_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ['-occurred_at'],
            },
        ),
        migrations.CreateModel(
            name='KnowledgeNode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('node_type', models.CharField(choices=[('user', 'User'), ('product', 'Product'), ('category', 'Category'), ('query', 'Query')], db_index=True, max_length=20)),
                ('external_id', models.CharField(db_index=True, max_length=255)),
                ('properties', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='RAGDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doc_type', models.CharField(choices=[('faq', 'FAQ'), ('policy', 'Policy'), ('catalog', 'Catalog'), ('guide', 'Guide')], db_index=True, default='faq', max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('token_count', models.IntegerField(default=0)),
                ('embedding_hint', models.JSONField(blank=True, default=list)),
                ('embedding', models.JSONField(blank=True, default=list)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='RecommendationCache',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_id', models.IntegerField(unique=True)),
                ('recommended_book_ids', models.JSONField(default=list)),
                ('reason', models.CharField(default='collaborative_filtering', max_length=100)),
                ('generated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='SearchHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_id', models.IntegerField()),
                ('query', models.CharField(max_length=255)),
                ('searched_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ViewHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_id', models.IntegerField()),
                ('book_id', models.IntegerField()),
                ('viewed_at', models.DateTimeField(auto_now_add=True)),
                ('view_duration_secs', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='KnowledgeEdge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relation_type', models.CharField(db_index=True, max_length=50)),
                ('weight', models.FloatField(default=0.0)),
                ('evidence_count', models.IntegerField(default=0)),
                ('last_event_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='out_edges', to='app.knowledgenode')),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='in_edges', to='app.knowledgenode')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='knowledgenode',
            unique_together={('node_type', 'external_id')},
        ),
        migrations.AlterUniqueTogether(
            name='knowledgeedge',
            unique_together={('source', 'target', 'relation_type')},
        ),
    ]
