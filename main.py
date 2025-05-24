import asyncio
import os
import uuid
from datetime import datetime

import supabase
import uvicorn
from fastapi import FastAPI, APIRouter, UploadFile, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.params import Depends, File
from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTasks
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import StreamingResponse

from enums import HomeworkAssistanceRunState, MediaUploadState
from models import Media
from request_models import CreateServerRequest, CreateServerResponse, CreateUserRequest, CreateUserResponse, \
    UserWithIdModel, CreateHomeworkAssistantRunRequest, CreateHomeworkAssistantRunResponse, HomeworkAssistanceRunStatus, \
    Message, GetHomeworkAssistanceRunStatusResponse, GetHomeworkAssistanceRunTasksResponse, TaskResponse
from services.HomeworkService import HomeworkService, StepLogicFactory
from services.UserService import UserService
from utils.db import sessionmanager, get_db
from utils.dependencies import get_user_service, get_homework_service
from utils.utils import get_supabase_client

user_router = APIRouter(prefix="/user")

homework_assistant_router = APIRouter(prefix="/homework-assistant")

@user_router.post("", tags=["user"])
async def create_user(create_user_request: CreateUserRequest, user_service: UserService = Depends(get_user_service), session: AsyncSession = Depends(get_db)) -> CreateUserResponse:
    user = await user_service.create_user(request=create_user_request, session=session)
    return CreateUserResponse(
        user=UserWithIdModel(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
        )

    )


@user_router.get("/{user_id}", tags=["user"])
async def get_user(user_id: str, user_service: UserService = Depends(get_user_service), session: AsyncSession = Depends(get_db)) -> UserWithIdModel:
    user = await user_service.get_user_by_auth_user_id(session=session, auth_user_id=user_id)
    return UserWithIdModel(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
    )


@homework_assistant_router.post("", tags=["homework"])
async def trigger_homework_assistance_run(create_homework_assistant_run_request: CreateHomeworkAssistantRunRequest, background_tasks: BackgroundTasks, homework_service: HomeworkService = Depends(get_homework_service), session: AsyncSession = Depends(get_db)) -> CreateHomeworkAssistantRunResponse:
    homework_assistance_run = await homework_service.create_homework_assistance_run(request=create_homework_assistant_run_request, session=session)
    for step in homework_assistance_run.steps:
        logic = StepLogicFactory.resolve(step)
        background_tasks.add_task(logic.run, homework_assistance_run.id)
    return CreateHomeworkAssistantRunResponse(
        homework_run_id=homework_assistance_run.id,
    )


@homework_assistant_router.get("/{homework_assistance_run_id}", tags=["homework"])
async def get_homework_assistance_run_state(homework_assistance_run_id: str, homework_service: HomeworkService = Depends(get_homework_service), session: AsyncSession = Depends(get_db)) -> HomeworkAssistanceRunStatus:
    homework_assistance_run = await homework_service.get_run(homework_assistance_run_id=homework_assistance_run_id, session=session)
    return HomeworkAssistanceRunStatus(
        homework_assistance_run_id=homework_assistance_run.id,
        labels=homework_assistance_run.labels,
        state=HomeworkAssistanceRunState[homework_assistance_run.state].value,  # type: ignore
        explanation=homework_assistance_run.explanation
    )


@homework_assistant_router.post("/chat/{homework_assistance_run_id}", tags=["homework"])
async def chat(homework_assistance_run_id: str, messages: list[Message], homework_service: HomeworkService = Depends(get_homework_service), session: AsyncSession = Depends(get_db)):
    return StreamingResponse(homework_service.on_chat_message(session=session, homework_assistance_run_id=homework_assistance_run_id, messages=messages), media_type="text/plain")


@user_router.post("/{user_id}/upload-homework/", tags=["user"])
async def upload_homework(
    user_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    homework_service: HomeworkService = Depends(get_homework_service),
    session: AsyncSession = Depends(get_db),
    supabase_client: supabase.AsyncClient = Depends(get_supabase_client)
) -> CreateHomeworkAssistantRunResponse:
    SUPABASE_BUCKET = "homework-files"
    contents = await file.read()

    filename = f"{uuid.uuid4()}_{file.filename}"
    storage_path = f"{user_id}/homeworks/{filename}"
    media = Media(
        id=str(uuid.uuid4()),
        path=storage_path,
        state=MediaUploadState.PENDING,
    )
    session.add(media)
    homework_assistance_run = await homework_service.create_homework_assistance_run(
        request=CreateHomeworkAssistantRunRequest(
            file_id=media.id,
            user_id=user_id,
        ),
        session=session
    )
    media.run_id = homework_assistance_run.id
    await session.commit()
    await session.refresh(homework_assistance_run)

    for step in homework_assistance_run.steps:
        logic = StepLogicFactory.resolve(step)
        background_tasks.add_task(logic.run, homework_assistance_run.id)

    try:
        await supabase_client.storage.from_(SUPABASE_BUCKET).upload(storage_path, contents)
    except Exception as e:
        media.state = MediaUploadState.FAILED
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
    else:
        media.state = MediaUploadState.SUCCESS
    finally:
        session.add(media)
        await session.commit()
        await session.refresh(media)
        await session.refresh(homework_assistance_run)

    return CreateHomeworkAssistantRunResponse(
        homework_assistance_run_id=homework_assistance_run.id,
    )


@homework_assistant_router.get("/status/{homework_assistance_run_id}", tags=["homework"])
async def get_homework_assistance_run_status(
        homework_assistance_run_id: str,
        homework_service: HomeworkService = Depends(get_homework_service),
        session: AsyncSession = Depends(get_db),
) -> GetHomeworkAssistanceRunStatusResponse:
    step_states = await homework_service.get_homework_assistant_run_steps_states(homework_assistance_run_id=homework_assistance_run_id, session=session)
    return step_states


@homework_assistant_router.get("/run/{homework_assistance_run_id}/tasks", response_model=GetHomeworkAssistanceRunTasksResponse, tags=["homework"])
async def get_homework_assistance_run_tasks(
        homework_assistance_run_id: str,
        homework_service: HomeworkService = Depends(get_homework_service),
        session: AsyncSession = Depends(get_db),
) -> GetHomeworkAssistanceRunTasksResponse:
    homework_assistance_run = await homework_service.get_run(session=session, homework_assistance_run_id=homework_assistance_run_id)
    return GetHomeworkAssistanceRunTasksResponse(
        homework_assistance_run_id=homework_assistance_run.id,
        tasks=[TaskResponse(
            id=task.id,
            key=task.key,
            description=task.description,
            concepts=task.concepts
        ) for task in homework_assistance_run.tasks]
    )


def custom_generate_unique_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"

def use_route_names_as_operation_ids(route: APIRoute):
    route.operation_id = route.name
    return route.name



app = FastAPI(openapi_tags=[
    {
        "name": "User",
        "description": "Operations related to users"
    },
    {
        "name": "Homework",
        "description": "Operations related to the homework assistant"
    }
],
    generate_unique_id_function=use_route_names_as_operation_ids,  # we’ll override it ourselves

)


app.include_router(user_router)

app.include_router(homework_assistant_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



if __name__ == "__main__":
    import subprocess
    asyncio.run(sessionmanager.create_tables())
    subprocess.run(["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])
