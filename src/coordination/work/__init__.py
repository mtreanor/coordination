"""The work: versions of the work, each implementing the Work interface."""

from .base import Work, WorkEvent, WorkFact
from .stub import StubWork

WORKS = {"stub": StubWork}
"""Every work a Run can be configured with, by name. Add a new version here."""

__all__ = ["WORKS", "StubWork", "Work", "WorkEvent", "WorkFact"]
