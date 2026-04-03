import logging
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.mailings.services.importer import import_mailings_from_xlsx

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import mailings from an XLSX file and send emails'

    def add_arguments(self, parser):
        parser.add_argument(
            'filepath',
            type=str,
            help='Path to the XLSX file',
        )

    def handle(self, *args, **options):
        filepath = Path(options['filepath'])

        if not filepath.exists():
            raise CommandError(f'File not found: {filepath}')

        if filepath.suffix.lower() != '.xlsx':
            raise CommandError(f'Expected .xlsx file, got: {filepath.suffix}')

        self.stdout.write(f'Importing from {filepath}…')

        try:
            result = import_mailings_from_xlsx(filepath)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(str(result))