import os

from services.HomeworkService import HomeworkService
from services.UserService import UserService


def get_user_service() -> UserService:
    return UserService()


def get_homework_service() -> HomeworkService:
    return HomeworkService()


