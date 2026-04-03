from io import BytesIO
from unittest.mock import patch

import openpyxl
from django.test import TestCase

from apps.mailings.models import MailingRecord
from apps.mailings.services.importer import import_mailings_from_xlsx


def make_xlsx(rows: list[dict]) -> BytesIO:
    """Helper — create an in-memory xlsx file from a list of dicts."""
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws
    headers = ['external_id', 'user_id', 'email', 'subject', 'message']
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h) for h in headers])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


@patch('apps.mailings.services.importer.send_email')
class ImportMailingsTest(TestCase):

    def test_creates_new_records(self, mock_send):
        buf = make_xlsx([
            {'external_id': 'ext-1', 'user_id': '1', 'email': 'a@test.com', 'subject': 'Hi', 'message': 'Hello'},
            {'external_id': 'ext-2', 'user_id': '2', 'email': 'b@test.com', 'subject': 'Hi', 'message': 'Hello'},
        ])
        result = import_mailings_from_xlsx(buf)

        self.assertEqual(result.total, 2)
        self.assertEqual(result.created, 2)
        self.assertEqual(result.skipped, 0)
        self.assertEqual(result.failed, 0)
        self.assertEqual(mock_send.call_count, 2)

    def test_skips_already_sent(self, mock_send):
        MailingRecord.objects.create(
            external_id='ext-1', user_id='1', email='a@test.com',
            subject='Hi', message='Hello', status=MailingRecord.Status.SENT,
        )
        buf = make_xlsx([
            {'external_id': 'ext-1', 'user_id': '1', 'email': 'a@test.com', 'subject': 'Hi', 'message': 'Hello'},
        ])
        result = import_mailings_from_xlsx(buf)

        self.assertEqual(result.skipped, 1)
        mock_send.assert_not_called()

    def test_retries_failed(self, mock_send):
        MailingRecord.objects.create(
            external_id='ext-1', user_id='1', email='a@test.com',
            subject='Hi', message='Hello', status=MailingRecord.Status.FAILED,
        )
        buf = make_xlsx([
            {'external_id': 'ext-1', 'user_id': '1', 'email': 'a@test.com', 'subject': 'Hi', 'message': 'Hello'},
        ])
        result = import_mailings_from_xlsx(buf)

        self.assertEqual(result.skipped, 0)
        mock_send.assert_called_once()
        self.assertEqual(MailingRecord.objects.get(external_id='ext-1').status, MailingRecord.Status.SENT)

    def test_missing_required_field(self, mock_send):
        buf = make_xlsx([
            {'external_id': 'ext-1', 'user_id': '1', 'email': None, 'subject': 'Hi', 'message': 'Hello'},
        ])
        result = import_mailings_from_xlsx(buf)

        self.assertEqual(result.failed, 1)
        self.assertEqual(result.total, 1)
        mock_send.assert_not_called()

    def test_send_failure_marks_record_failed(self, mock_send):
        mock_send.side_effect = Exception('SMTP error')
        buf = make_xlsx([
            {'external_id': 'ext-1', 'user_id': '1', 'email': 'a@test.com', 'subject': 'Hi', 'message': 'Hello'},
        ])
        result = import_mailings_from_xlsx(buf)

        self.assertEqual(result.failed, 1)
        self.assertEqual(MailingRecord.objects.get(external_id='ext-1').status, MailingRecord.Status.FAILED)

    def test_empty_file(self, mock_send):
        wb = openpyxl.Workbook()
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)

        result = import_mailings_from_xlsx(buf)

        self.assertEqual(result.total, 0)
        mock_send.assert_not_called()