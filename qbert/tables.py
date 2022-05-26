"""Defines the Piccolo table schemas."""
from piccolo.columns import JSONB, UUID, Integer, Text, Timestamptz
from piccolo.table import Table

from qbert.enums import JobStatus


class Job(Table, tablename="qbert_job"):
    """Job table schema."""

    id = UUID(primary_key=True)
    created_at = Timestamptz(null=False)
    updated_at = Timestamptz(null=False)
    scheduled_for = Timestamptz(null=False, required=True, index=True)
    failed_attempts = Integer(null=False, default=0)
    status = Integer(
        null=False, choices=JobStatus, default=JobStatus.QUEUED, index=True
    )
    message_type = Text(null=False, required=True)
    message = JSONB(null=False, required=True)
