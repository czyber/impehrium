from pydantic import BaseModel


class CreateServerRequest(BaseModel):
    name: str
