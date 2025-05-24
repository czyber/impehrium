import datetime
from typing import Literal

from pydantic import BaseModel

from enums import HomeworkAssistanceRunState, HomeworkAssistanceRunStepState, HomeworkAssistanceRunStepName


class CreateServerRequest(BaseModel):
    name: str


class UserModel(BaseModel):
    auth_user_id: str
    first_name: str
    last_name: str


class UserWithIdModel(BaseModel):
    id: str
    first_name: str
    last_name: str

class HomeworkAssistanceRunStatus(BaseModel):
    homework_assistance_run_id: str
    labels: list[str]
    state: HomeworkAssistanceRunState
    explanation: str | None


class CreateUserRequest(BaseModel):
    user: UserModel


class CreateServerResponse(BaseModel):
    id: str
    name: str
    started_at: datetime.datetime
    ended_at: datetime.datetime | None


class CreateHomeworkAssistantRunRequest(BaseModel):
    user_id: str
    file_id: str


class Message(BaseModel):
    role: Literal["user", "system", "assistant"]
    content: str


class CreateUserResponse(BaseModel):
    user: UserWithIdModel


class CreateHomeworkAssistantRunResponse(BaseModel):
    homework_assistance_run_id: str


class GetHomeworkAssistanceRunStatusResponse(BaseModel):
    homework_assistance_run_id: str
    step_states: list[dict]


class TaskResponse(BaseModel):
    id: str
    key: str
    description: str
    concepts: list[str]


class GetHomeworkAssistanceRunTasksResponse(BaseModel):
    homework_assistance_run_id: str
    tasks: list[TaskResponse]
