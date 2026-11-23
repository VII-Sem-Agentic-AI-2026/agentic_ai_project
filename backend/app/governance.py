"""Pure domain rules; transport authentication and persistence are separate layers."""
from dataclasses import dataclass, field
from enum import Enum


class Role(str, Enum):
    STUDENT = "student"
    FACULTY = "faculty"


class Status(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"


@dataclass(frozen=True)
class Actor:
    id: str
    role: Role


@dataclass(frozen=True)
class Report:
    student_id: str
    score: int
    evidence_ids: tuple[str, ...]

    def __post_init__(self):
        if not self.student_id or type(self.score) is not int or not 0 <= self.score <= 100:
            raise ValueError("Report requires a student and an integer score from 0 to 100")
        if not self.evidence_ids or any(not item for item in self.evidence_ids):
            raise ValueError("Evidence references are required")


@dataclass
class Review:
    report: Report
    status: Status = Status.DRAFT
    approved_by: str | None = None
    versions: list[Report] = field(default_factory=list)
    active_version: int | None = None
    events: list[dict] = field(default_factory=list)

    def submit(self, checks: dict[str, bool]):
        if self.status != Status.DRAFT:
            raise ValueError("Only a draft can enter review")
        if not checks or not all(value is True for value in checks.values()):
            raise ValueError("All validation checks must pass")
        self.status = Status.REVIEW
        self.events.append({"action": "validated", "checks": dict(checks)})

    def approve(self, actor: Actor):
        self._faculty(actor)
        if self.status != Status.REVIEW:
            raise ValueError("Only validated reports can be approved")
        self.approved_by = actor.id
        self.status = Status.APPROVED
        self.versions.append(self.report)
        self.active_version = len(self.versions)
        self.events.append({"action": "published", "actor": actor.id, "version": self.active_version})

    def revise(self, actor: Actor, report: Report):
        self._faculty(actor)
        if report.student_id != self.report.student_id:
            raise ValueError("Revision cannot change the report owner")
        self.report = report
        self.status = Status.DRAFT
        self.approved_by = None
        self.events.append({"action": "revised", "actor": actor.id})

    def published(self, actor: Actor) -> Report:
        if actor.role != Role.FACULTY and actor.id != self.report.student_id:
            raise PermissionError("Report belongs to another student")
        if self.active_version is None:
            raise ValueError("No approved report has been published")
        return self.versions[self.active_version - 1]

    def rollback(self, actor: Actor, version: int):
        self._faculty(actor)
        if type(version) is not int or not 1 <= version <= len(self.versions):
            raise ValueError("Unknown published version")
        self.active_version = version
        self.events.append({"action": "rollback", "actor": actor.id, "version": version})

    @staticmethod
    def _faculty(actor: Actor):
        if actor.role != Role.FACULTY:
            raise PermissionError("Faculty authority required")
