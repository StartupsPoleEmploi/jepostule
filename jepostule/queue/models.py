from django.db import models

from . import serialize

class Message(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    topic = models.CharField(max_length=64, db_index=True)
    value = models.BinaryField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def value_str(self):
        return self.value_bytes.decode()

    @property
    def value_bytes(self):
        return bytes(self.value)

    @property
    def value_readable(self):
        """
        This is for readability only. DO NOT use as a functional value in the
        rest of the application.
        """
        try:
            return serialize.loads(self.value_bytes)
        except serialize.DecodeError:
            pass
        try:
            return self.value_str
        except UnicodeDecodeError:
            pass
        return self.value_bytes


class FailedMessage(Message):
    """
    Message for which processing failed. It is important that such messages are
    either archived, or retried (and deleted).
    """
    STATUS_NEW = 'new'
    STATUS_ARCHIVED = 'archived'
    STATUSES = (
        (STATUS_NEW, 'New'),
        (STATUS_ARCHIVED, 'Archived'),
    )

    status = models.CharField(max_length=32, choices=STATUSES, db_index=True, default=STATUS_NEW)
    exception = models.CharField(max_length=64, blank=True)
    traceback = models.TextField(blank=True)

    class Meta:
        ordering = ['created_at']

    def archive(self):
        """
        Archived messages are not deleted, but they won't be retried
        """
        self.status = self.STATUS_ARCHIVED
        self.save(update_fields=['status'])


class DelayedMessage(Message):
    """
    Message to be produced at a later time.
    """
    until = models.DateTimeField(db_index=True)
