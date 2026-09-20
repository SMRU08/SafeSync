from typing import Optional
from pydantic import BaseModel


class RootResponse(BaseModel):
    project: str
    status: str


class HealthResponse(BaseModel):
    status: str
    database: Optional[str] = None
    ai_engine: Optional[str] = "Not Connected"
