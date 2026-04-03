import logging
from dataclasses import dataclass, field
from pathlib import Path
from io import BytesIO


import openpyxl

from apps.mailings.models import MailingRecord
from apps.mailings.services.email_sender import send_email

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {'external_id', 'user_id', 'email', 'subject', 'message'}


@dataclass
class ImportResult:
    total: int = 0
    created: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        lines = [
            f'Processed : {self.total}',
            f'Created   : {self.created}',
            f'Skipped   : {self.skipped}',
            f'Failed    : {self.failed}',
        ]
        if self.errors:
            lines.append('Errors:')
            lines.extend(f'  {e}' for e in self.errors)
        return '\n'.join(lines)


def import_mailings_from_xlsx(filepath: str | Path | BytesIO) -> ImportResult:
    result = ImportResult()
    workbook = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    sheet = workbook.active
    rows = iter(sheet.rows) # type: ignore

    try:
        header_row = next(rows)
    except StopIteration:
        logger.warning('File %s is empty', filepath)
        return result

    headers = [cell.value for cell in header_row]
    missing = REQUIRED_COLUMNS - set(headers) # type: ignore
    if missing:
        raise ValueError(f'Missing required columns: {missing}')

    col = {name: idx for idx, name in enumerate(headers)}

    for row_num, row in enumerate(rows, start=2):
        result.total += 1
        values = [cell.value for cell in row]

        try:
            data = _parse_row(values, col, row_num)
        except ValueError as exc:
            result.failed += 1
            result.errors.append(str(exc))
            continue

        record, created = MailingRecord.objects.get_or_create(
            external_id=data['external_id'],
            defaults={**data, 'status': MailingRecord.Status.PENDING},
        )

        if not created and record.status == MailingRecord.Status.SENT:
            logger.debug('Row %d: already sent, skipping (external_id=%s)', row_num, record.external_id)
            result.skipped += 1
            continue

        if created:
            result.created += 1

        _send_and_update(record, result, row_num)

    workbook.close()
    return result


def _parse_row(values: list, col: dict, row_num: int) -> dict:
    """Extract and validate a single row. Raises ValueError on missing required fields."""
    data = {key: values[idx] for key, idx in col.items()}

    for field_name in REQUIRED_COLUMNS:
        if not data.get(field_name):
            raise ValueError(f'Row {row_num}: missing value for {field_name!r}')

    return data


def _send_and_update(record: MailingRecord, result: ImportResult, row_num: int) -> None:
    """Send email and update record status."""
    try:
        send_email(email=record.email, subject=record.subject, message=record.message)
        record.status = MailingRecord.Status.SENT
    except Exception as exc:
        logger.error('Row %d: failed to send (external_id=%s): %s', row_num, record.external_id, exc)
        record.status = MailingRecord.Status.FAILED
        result.failed += 1
        result.errors.append(f'Row {row_num}: send failed — {exc}')
    finally:
        record.save(update_fields=['status', 'updated_at'])