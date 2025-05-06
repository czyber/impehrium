import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Server
from request_models import CreateServerRequest
from datetime import datetime


class ServerService:
    async def create_server(self, session: AsyncSession, request: CreateServerRequest) -> Server:
        server = Server(
            id=str(uuid.uuid4()),
            name=request.name,
            started_at=datetime.now(),
        )
        session.add(server)
        await session.commit()
        await session.refresh(server)
        return server

    async def delete_server(self, session: AsyncSession, server_id: str) -> Server:
        async with session:
            statement = select(Server).filter(Server.id == server_id)
            promise = await session.execute(statement)
            server = promise.scalar()
        await session.delete(server)
        await session.commit()
        return server

