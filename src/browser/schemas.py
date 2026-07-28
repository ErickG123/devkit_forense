from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BrowserHistoryRequest(BaseModel):
    browser: str = Field(..., description="Nome do navegador (ex: chrome, firefox)")
    limit: Optional[int] = Field(None, description="Limite de registros a retornar")


class BrowserHistoryResponse(BaseModel):
    status: str
    data: List[Dict[str, Any]]
