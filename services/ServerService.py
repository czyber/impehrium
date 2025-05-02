import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Server
from request_models import CreateServerRequest
from datetime import datetime


class ServerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_server(self, request: CreateServerRequest) -> Server:
        server = Server(
            id=str(uuid.uuid4()),
            name=request.name,
            started_at=datetime.now(),
        )
        self.session.add(server)
        await self.session.commit()
        await self.session.refresh(server)
        return server

    async def delete_server(self, server_id: str) -> Server:
        async with self.session:
            statement = select(Server).filter(Server.id == server_id)
            promise = await self.session.execute(statement)
            server = promise.scalar()
        await self.session.delete(server)
        await self.session.commit()
        return server

