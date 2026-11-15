from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str


class DBHealthResponse(BaseModel):
    status: str
    database: str
    detail: str | None = None
