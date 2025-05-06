import asyncio
from datetime import datetime

import uvicorn
from fastapi import FastAPI, APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTasks
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import StreamingResponse

from enums import HomeworkAssistanceRunState
from models import Server
from request_models import CreateServerRequest, CreateServerResponse, CreateUserRequest, CreateUserResponse, \
    UserWithIdModel, CreateHomeworkAssistantRunRequest, CreateHomeworkAssistantRunResponse, HomeworkAssistanceRunStatus, \
    Message
from services.HomeworkService import HomeworkService, StepLogicFactory
from services.ServerService import ServerService
from services.UserService import UserService
from utils.db import sessionmanager, get_db
from utils.dependencies import get_server_service, get_user_service, get_homework_service

server_router = APIRouter(prefix="/server")

user_router = APIRouter(prefix="/user")

homework_assistant_router = APIRouter(prefix="/homework-assistant")

@server_router.post("")
async def create_server(create_server_request: CreateServerRequest, server_service: ServerService = Depends(get_server_service), session: AsyncSession = Depends(get_db)) -> CreateServerResponse:
    server = await server_service.create_server(create_server_request, session=session)
    return CreateServerResponse(
        id=server.id,
        name=server.name,
        started_at=server.started_at,
        ended_at=server.ended_at,
    )


@server_router.delete("/{server_id}")
async def delete_server(server_id: str, server_service: ServerService = Depends(get_server_service), session: AsyncSession = Depends(get_db)) -> CreateServerResponse:
    server = await server_service.delete_server(server_id, session=session)
    return CreateServerResponse(
        id=server.id,
        name=server.name,
        started_at=server.started_at,
        ended_at=server.ended_at,
    )


@user_router.post("")
async def create_user(create_user_request: CreateUserRequest, user_service: UserService = Depends(get_user_service), session: AsyncSession = Depends(get_db)) -> CreateUserResponse:
    user = await user_service.create_user(request=create_user_request, session=session)
    return CreateUserResponse(
        user=UserWithIdModel(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
        )

    )


@user_router.get("/{user_id}")
async def get_user(user_id: str, user_service: UserService = Depends(get_user_service), session: AsyncSession = Depends(get_db)) -> UserWithIdModel:
    user = await user_service.get_user_by_auth_user_id(session=session, auth_user_id=user_id)
    return UserWithIdModel(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
    )


@homework_assistant_router.post("")
async def trigger_homework_assistance_run(create_homework_assistant_run_request: CreateHomeworkAssistantRunRequest, background_tasks: BackgroundTasks, homework_service: HomeworkService = Depends(get_homework_service), session: AsyncSession = Depends(get_db)) -> CreateHomeworkAssistantRunResponse:
    homework_assistance_run = await homework_service.create_homework_assistance_run(request=create_homework_assistant_run_request, session=session)
    for step in homework_assistance_run.steps:
        logic = StepLogicFactory.resolve(step)
        background_tasks.add_task(logic.run, homework_assistance_run.id)
    return CreateHomeworkAssistantRunResponse(
        homework_run_id=homework_assistance_run.id,
    )


@homework_assistant_router.get("/{homework_assistance_run_id}")
async def get_homework_assistance_run_state(homework_assistance_run_id: str, homework_service: HomeworkService = Depends(get_homework_service), session: AsyncSession = Depends(get_db)) -> HomeworkAssistanceRunStatus:
    homework_assistance_run = await homework_service.get_run(homework_assistance_run_id, session=session)
    return HomeworkAssistanceRunStatus(
        homework_assistance_run_id=homework_assistance_run.id,
        labels=homework_assistance_run.labels,
        state=HomeworkAssistanceRunState[homework_assistance_run.state].value,  # type: ignore
    )


@homework_assistant_router.post("/chat/{homework_assistance_run_id}")
async def chat(homework_assistance_run_id: str, messages: list[Message], homework_service: HomeworkService = Depends(get_homework_service), session: AsyncSession = Depends(get_db)):
    return StreamingResponse(homework_service.on_chat_message(session=session, homework_assistance_run_id=homework_assistance_run_id, messages=messages), media_type="text/plain")


app = FastAPI()

app.include_router(server_router)
app.include_router(user_router)

app.include_router(homework_assistant_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to frontend domain
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import subprocess
    asyncio.run(sessionmanager.create_tables())
    subprocess.run(["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])
