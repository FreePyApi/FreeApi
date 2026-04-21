from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ApiKeyCreateRequest(BaseModel):
  description: Optional[str] = Field(default=None, max_length=200)
  expires_at: Optional[datetime] = None
