from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, ConfigDict


class RootResponse(BaseModel):
    project: str
    status: str


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str
    api: Optional[Dict[str, Any]] = None
    database: Optional[Union[str, Dict[str, Any]]] = None
    database_connected: Optional[bool] = None
    ai_engine: Optional[Union[str, Dict[str, Any]]] = "Not Connected"
    ai_status: Optional[str] = None
    model_loaded: Optional[bool] = None
    websocket: Optional[Dict[str, Any]] = None
