import asyncio
import os
import uuid
from datetime import datetime

import supabase
import uvicorn
from fastapi import FastAPI, APIRouter, UploadFile, HTTPException
from fastapi.params import Depends, File
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTasks
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import StreamingResponse

from enums import HomeworkAssistanceRunState, MediaUploadState
from models import Media
from request_models import CreateServerRequest, CreateServerResponse, CreateUserRequest, CreateUserResponse, \
    UserWithIdModel, CreateHomeworkAssistantRunRequest, CreateHomeworkAssistantRunResponse, HomeworkAssistanceRunStatus, \
    Message, GetHomeworkAssistanceRunStatusResponse
from services.HomeworkService import HomeworkService, StepLogicFactory
from services.UserService import UserService
from utils.db import sessionmanager, get_db
from utils.dependencies import get_user_service, get_homework_service


user_router = APIRouter(prefix="/user")

homework_assistant_router = APIRouter(prefix="/homework-assistant")

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


@user_router.post("/{user_id}/upload-homework/")
async def upload_homework(
    user_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    homework_service: HomeworkService = Depends(get_homework_service),
    session: AsyncSession = Depends(get_db),
) -> CreateHomeworkAssistantRunResponse:
    SUPABASE_URL = os.environ["SUPABASE_URL"]
    SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    SUPABASE_BUCKET = "homework-files"
    supabase_client: supabase.AsyncClient = await supabase.acreate_client(SUPABASE_URL, SUPABASE_KEY)
    contents = await file.read()

    filename = f"{uuid.uuid4()}_{file.filename}"
    storage_path = f"{user_id}/homeworks/{filename}"
    media = Media(
        path=storage_path,
        state=MediaUploadState.PENDING,
    )
    session.add(media)
    await session.commit()
    await session.refresh(media)

    homework_assistance_run = await homework_service.create_homework_assistance_run(
        request=CreateHomeworkAssistantRunRequest(
            file_id=media.id,
            user_id=user_id,
        ),
        session=session
    )

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
        await session.commit()
        await session.refresh(media)
        await session.refresh(homework_assistance_run)

    return CreateHomeworkAssistantRunResponse(
        homework_assistance_run_id=homework_assistance_run.id,
    )


@homework_assistant_router.get("/status/{homework_assistance_run_id}")
async def get_homework_assistance_run_status(
        homework_assistance_run_id: str,
        homework_service: HomeworkService = Depends(get_homework_service),
        session: AsyncSession = Depends(get_db),
) -> GetHomeworkAssistanceRunStatusResponse:
    step_states = await homework_service.get_homework_assistant_run_steps_states(homework_assistance_run_id=homework_assistance_run_id, session=session)
    return step_states


app = FastAPI()

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
