import datetime

from pydantic import BaseModel, UUID4


class CreateServerResponse(BaseModel):
    id: str
    name: str
    started_at: datetime.datetime
    ended_at: datetime.datetime | None
