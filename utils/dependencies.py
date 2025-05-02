from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.ServerService import ServerService
from utils.db import get_db


def get_server_service(db: AsyncSession = Depends(get_db)) -> ServerService:
    return ServerService(db)
