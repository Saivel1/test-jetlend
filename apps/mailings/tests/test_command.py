from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


class ImportMailingsCommandTest(TestCase):

    def test_file_not_found(self):
        with self.assertRaises(CommandError, msg='File not found'):
            call_command('import_mailings', 'nonexistent.xlsx')

    def test_wrong_extension(self, tmp_path=None):
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            f.write(b'data')
            name = f.name
        try:
            with self.assertRaises(CommandError, msg='Expected .xlsx'):
                call_command('import_mailings', name)
        finally:
            os.unlink(name)

    @patch('apps.mailings.services.importer.send_email')
    def test_successful_import_prints_result(self, mock_send):
        import tempfile
        import os
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        assert ws
        ws.append(['external_id', 'user_id', 'email', 'subject', 'message'])
        ws.append(['ext-1', '1', 'a@test.com', 'Hi', 'Hello'])
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            name = f.name
        wb.save(name)
        try:
            out = StringIO()
            call_command('import_mailings', name, stdout=out)
            output = out.getvalue()
            self.assertIn('Created', output)
            self.assertIn('1', output)
        finally:
            os.unlink(name)