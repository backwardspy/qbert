"""
Defines the public task queue interface.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Type
from uuid import UUID

import ulid
from piccolo.utils.encoding import load_json
from pydantic import BaseModel

from qbert.enums import JobStatus
from qbert.tables import Job as JobDB


@dataclass(frozen=True)
class Job:
    """Combines a message model with a unique ID."""

    id: UUID
    message: BaseModel


def squash(query: str) -> str:
    """Turns a nicely formatted & indented query into a single line."""
    return " ".join(query.strip().replace("\n", " ").split())


PULL_QUERY = squash(
    """
    UPDATE qbert_job
    SET status = {}, updated_at = {}
    WHERE id IN (
        SELECT id
        FROM qbert_job
        WHERE status = {}
        AND scheduled_for <= {}
        AND failed_attempts < {}
        ORDER BY scheduled_for
        FOR UPDATE SKIP LOCKED
        LIMIT {}
    )
    RETURNING *
    """
)

FAIL_JOB_QUERY = squash(
    """
    UPDATE qbert_job
    SET
        failed_attempts = failed_attempts + 1,
        status = CASE
            WHEN failed_attempts < {} - 1 THEN {}::int
            ELSE {}::int
        END
    WHERE id = {}
    """
)


class Queue:
    """Represents a queue of jobs."""

    def __init__(
        self, message_types: list[Type[BaseModel]], *, max_attempts: int = 3
    ) -> None:
        self.max_attempts = max_attempts
        self.message_types = {
            message_type.__name__: message_type for message_type in message_types
        }

    def _make_job(self, job: dict) -> Job:
        message_type = self.message_types[job["message_type"]]
        message_content = load_json(job["message"])
        return Job(id=job["id"], message=message_type(**message_content))

    async def push(
        self, message: BaseModel, scheduled_for: datetime | None = None
    ) -> None:
        """Push a new job to the queue."""
        message_type = type(message).__name__
        if message_type not in self.message_types:
            raise ValueError(
                f"Unknown message type: {message_type}. "
                "Please ensure this message type is in the list of message types "
                "passed to the Queue constructor."
            )

        await JobDB.insert(
            JobDB(
                id=ulid.new().uuid,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                scheduled_for=scheduled_for or datetime.utcnow(),
                message_type=message_type,
                message=message.dict(),
            )
        )

    async def pull(self, number_of_jobs: int = 1) -> list[Job]:
        """
        Pull a number of jobs from the queue.
        This uses FOR UPDATE SKIP LOCKED to maximise concurrent performance.
        """
        jobs = await JobDB.raw(
            PULL_QUERY,
            JobStatus.RUNNING,
            datetime.utcnow(),
            JobStatus.QUEUED,
            datetime.utcnow(),
            self.max_attempts,
            number_of_jobs,
        )

        return [self._make_job(job) for job in jobs]

    async def delete_job(self, job_id: UUID) -> None:
        """Delete a job from the queue."""
        await JobDB.delete().where(JobDB.id == job_id)

    async def fail_job(self, job_id: UUID) -> None:
        """
        Fail a job. This will put the job back in the queue if it has any
        attempts remaining, or mark it as failed otherwise.
        """
        await JobDB.raw(
            FAIL_JOB_QUERY,
            self.max_attempts,
            JobStatus.QUEUED,
            JobStatus.FAILED,
            job_id,
        )

    async def clear(self) -> None:
        """Remove all jobs from the queue."""
        await JobDB.delete(force=True)
