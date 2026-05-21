import uuid

from django.conf import settings
from django.db import models


class ComparisonJob(models.Model):
    """One file-comparison run. Holds the uploaded bytes, the worker's status,
    and the comparison result. UUID PK so URLs are unguessable."""

    STATUS_PENDING = 'pending'
    STATUS_RUNNING = 'running'
    STATUS_DONE = 'done'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_RUNNING, 'Running'),
        (STATUS_DONE, 'Done'),
        (STATUS_FAILED, 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comparison_jobs',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)

    file_a_name = models.CharField(max_length=255)
    file_a_data = models.BinaryField()
    file_b_name = models.CharField(max_length=255)
    file_b_data = models.BinaryField()

    # Populated by the worker when the comparison completes.
    result_json = models.JSONField(null=True, blank=True)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
