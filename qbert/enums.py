"""Shared enumerations."""
from enum import IntEnum, auto


class JobStatus(IntEnum):
    """
    Enumeration of job statuses.
    Stored in the database as integers for better index performance.
    """

    QUEUED = auto()
    RUNNING = auto()
    FAILED = auto()
