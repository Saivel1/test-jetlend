import logging
from random import randint
from time import sleep

logger = logging.getLogger(__name__)


def send_email(*, email: str, subject: str, message: str) -> None:
    """Simulate sending an email by logging it with a random delay."""
    delay = randint(5, 20)
    logger.info('Sending email to %s (subject: %r)…', email, subject)
    sleep(delay)
    logger.info('Email sent to %s (subject: %r)', email, subject)