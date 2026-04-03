from django.db import models


class MailingRecord(models.Model):

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'

    external_id = models.CharField(max_length=255, unique=True, db_index=True)
    user_id = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=998)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Mailing Record'
        verbose_name_plural = 'Mailing Records'

    def __str__(self) -> str:
        return f'MailingRecord(external_id={self.external_id}, email={self.email}, status={self.status})'