from django.core.management.base import BaseCommand

from app.services import retrain_and_auto_switch


class Command(BaseCommand):
    help = 'Retrain behavior models and auto-switch to best snapshot by metric.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--models',
            nargs='*',
            default=['gru4rec', 'transformer', 'gnn'],
            choices=['markov', 'gru4rec', 'transformer', 'gnn'],
        )
        parser.add_argument('--min-transitions', type=int, default=1)
        parser.add_argument('--epochs', type=int, default=3)

    def handle(self, *args, **options):
        result = retrain_and_auto_switch(
            models=tuple(options['models']),
            min_transitions=options['min_transitions'],
            epochs=options['epochs'],
        )
        self.stdout.write(self.style.SUCCESS(f"Retrain result: {result}"))
