from django.core.management.base import BaseCommand

from app.services import sync_interactions_to_neo4j


class Command(BaseCommand):
    help = 'Sync InteractionEvent stream into Neo4j graph store.'

    def add_arguments(self, parser):
        parser.add_argument('--customer-id', type=int, default=None)
        parser.add_argument('--full-rebuild', action='store_true')

    def handle(self, *args, **options):
        result = sync_interactions_to_neo4j(
            customer_id=options.get('customer_id'),
            full_rebuild=options.get('full_rebuild', False),
        )
        self.stdout.write(self.style.SUCCESS(f"Neo4j sync result: {result}"))
