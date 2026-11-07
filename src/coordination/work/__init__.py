"""The work: versions of the work, each implementing the Work interface (ADR 0004, 0005, 0006)."""

from .base import Work, WorkDecision, WorkEvent, WorkFact
from .investment_club import InvestmentClubWork
from .not_my_bug import NotMyBugWork
from .stub import StubWork

WORKS = {"stub": StubWork, "investment-club": InvestmentClubWork, "not-my-bug": NotMyBugWork}
"""Every work a Run can be configured with, by name. Add a new version here."""

__all__ = ["WORKS", "InvestmentClubWork", "NotMyBugWork", "StubWork", "Work", "WorkDecision", "WorkEvent", "WorkFact"]
