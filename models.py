import datetime
import uuid
from collections.abc import Callable

from pydantic import UUID5, UUID4
from sqlalchemy import ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enums import HomeworkAssistanceRunStepState, HomeworkAssistanceRunState
from utils.db import Base


def uuid4_str() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(primary_key=True, default=uuid4_str)
    auth_user_id: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class HomeworkAssistanceRunStep(Base):
    __tablename__ = "homework_assistance_run_steps"
    id: Mapped[str] = mapped_column(primary_key=True, default=uuid4_str)
    step_name: Mapped[str]
    run_id: Mapped[str] = mapped_column(ForeignKey("homework_assistance_runs.id", ondelete="CASCADE"))
    state: Mapped[str] = mapped_column(default=HomeworkAssistanceRunStepState.PENDING.value)
    run: Mapped["HomeworkAssistanceRun"] = relationship(back_populates="steps")

    def finish(self):
        self.state = HomeworkAssistanceRunState.SUCCEEDED


class HomeworkAssistanceRun(Base):
    __tablename__ = "homework_assistance_runs"

    id: Mapped[str] = mapped_column(primary_key=True, default=uuid4_str)
    state: Mapped[str]
    labels: Mapped[list[str] | None] = mapped_column(JSONB)
    task: Mapped[str | None]
    explanation: Mapped[str | None]
    steps: Mapped[list[HomeworkAssistanceRunStep]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    @property
    def finished(self) -> bool:
        for step in self.steps:
            if step.state != HomeworkAssistanceRunStepState.SUCCEEDED.value:
                return False
        return True

    def get_step(self, step_name: str) -> HomeworkAssistanceRunStep | None:
        for step in self.steps:
            if step.step_name == step_name:
                return step

        return None


class Media(Base):
    __tablename__ = "media"
    id: Mapped[str] = mapped_column(primary_key=True, default=uuid4_str)
    path: Mapped[str]
    state: Mapped[str]


