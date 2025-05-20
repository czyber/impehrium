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
    homework_assistance_runs: Mapped["HomeworkAssistanceRun"] = relationship(
        back_populates="user",
        cascade="all, delete, delete-orphan",
    )

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


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[str] = mapped_column(primary_key=True, default=uuid4_str)
    key: Mapped[str]
    description: Mapped[str]
    concepts: Mapped[list[str]] = mapped_column(JSONB)

    run_id: Mapped[str] = mapped_column(ForeignKey("homework_assistance_runs.id", ondelete="CASCADE"))
    run: Mapped["HomeworkAssistanceRun"] = relationship(
        back_populates="tasks",
        foreign_keys=[run_id],
    )


class Media(Base):
    __tablename__ = "media"
    id: Mapped[str] = mapped_column(primary_key=True, default=uuid4_str)
    path: Mapped[str]
    state: Mapped[str]
    run_id: Mapped[str] = mapped_column(ForeignKey("homework_assistance_runs.id", ondelete="CASCADE"))
    run: Mapped["HomeworkAssistanceRun"] = relationship(
        back_populates="medias",
    )



class HomeworkAssistanceRun(Base):
    __tablename__ = "homework_assistance_runs"

    id: Mapped[str] = mapped_column(primary_key=True, default=uuid4_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    file_id: Mapped[str | None]
    user: Mapped["User"] = relationship(
        back_populates="homework_assistance_runs",
        foreign_keys=[user_id],
        lazy="selectin",
    )
    state: Mapped[str]
    labels: Mapped[list[str] | None] = mapped_column(JSONB)

    tasks: Mapped[list[Task]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys=[Task.run_id],  # explicitly specify foreign key here
    )

    selected_task_id: Mapped[str | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL")
    )
    selected_task: Mapped["Task | None"] = relationship(
        foreign_keys=[selected_task_id],
        lazy="joined"
    )

    explanation: Mapped[str | None]
    steps: Mapped[list[HomeworkAssistanceRunStep]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    medias: Mapped[list["Media"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys=[Media.run_id]
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




