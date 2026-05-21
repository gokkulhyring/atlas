"""Celery tasks for the atlasdemo app."""
import dataclasses
import math

from celery import shared_task

from .compare import CompareError, compare_files


class _BytesUpload:
    """File-like adapter for compare_files() that already-loaded bytes can use."""

    def __init__(self, data: bytes, name: str):
        self._data = data
        self.name = name

    def read(self) -> bytes:
        return self._data


def _to_json_safe(value):
    """Recursively convert pandas/numpy/NaN values into JSON-safe Python primitives.

    MySQL's JSON column type rejects `NaN`/`Infinity` (the JSON spec doesn't
    allow them). pandas hands us those for empty numeric cells, so we replace
    them with None before saving.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, (int, str)):
        return value
    if isinstance(value, dict):
        return {k: _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json_safe(v) for v in value]
    # numpy scalars (int64, float64, etc.) expose .item() to convert to native Python.
    if hasattr(value, 'item'):
        try:
            return _to_json_safe(value.item())
        except (ValueError, TypeError):
            pass
    return str(value)


@shared_task
def run_comparison(job_id: str) -> None:
    """Look up the ComparisonJob row, run the comparison, write the result back.
    Returns nothing — the status view reads the row directly."""
    from .models import ComparisonJob

    job = ComparisonJob.objects.get(pk=job_id)
    job.status = ComparisonJob.STATUS_RUNNING
    job.save(update_fields=['status'])

    try:
        file_a = _BytesUpload(bytes(job.file_a_data), job.file_a_name)
        file_b = _BytesUpload(bytes(job.file_b_data), job.file_b_name)
        result = compare_files(file_a, file_b)

        payload = dataclasses.asdict(result)
        payload['has_issues'] = result.has_issues
        payload['total_issues'] = result.total_issues
        job.result_json = _to_json_safe(payload)
        job.status = ComparisonJob.STATUS_DONE
        job.save(update_fields=['result_json', 'status'])
    except CompareError as exc:
        job.status = ComparisonJob.STATUS_FAILED
        job.error = str(exc)
        job.save(update_fields=['status', 'error'])
    except Exception as exc:
        # Any other crash: don't leave the row stuck at 'running'.
        job.status = ComparisonJob.STATUS_FAILED
        job.error = f'{type(exc).__name__}: {exc}'
        job.save(update_fields=['status', 'error'])
        raise  # re-raise so Celery logs the traceback
