from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    event: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = Field(default_factory=dict)
