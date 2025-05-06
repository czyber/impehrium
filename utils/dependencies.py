from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.HomeworkService import HomeworkService
from services.ServerService import ServerService
from services.UserService import UserService
from utils.db import get_db


def get_server_service() -> ServerService:
    return ServerService()


def get_user_service() -> UserService:
    return UserService()


def get_homework_service() -> HomeworkService:
    return HomeworkService()
