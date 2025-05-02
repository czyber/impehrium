import asyncio
from datetime import datetime

import uvicorn
from fastapi import FastAPI, APIRouter
from fastapi.params import Depends

from models import Server
from request_models import CreateServerRequest
from response_models import CreateServerResponse
from services.ServerService import ServerService
from utils.db import sessionmanager
from utils.dependencies import get_server_service

server_router = APIRouter(prefix="/server")


@server_router.post("/")
async def create_server(create_server_request: CreateServerRequest, server_service: ServerService = Depends(get_server_service)) -> CreateServerResponse:
    server = await server_service.create_server(create_server_request)
    return CreateServerResponse(
        id=server.id,
        name=server.name,
        started_at=server.started_at,
        ended_at=server.ended_at,
    )

@server_router.delete("/{server_id}")
async def delete_server(server_id: str, server_service: ServerService = Depends(get_server_service)) -> CreateServerResponse:
    server = await server_service.delete_server(server_id)
    return CreateServerResponse(
        id=server.id,
        name=server.name,
        started_at=server.started_at,
        ended_at=server.ended_at,
    )


app = FastAPI()
app.include_router(server_router)


if __name__ == "__main__":
    asyncio.run(sessionmanager.create_tables())
    uvicorn.run(app, host="0.0.0.0", port=8000)
