from typing import Any, Dict

from pydantic import BaseModel, Field


class MailAnalysisRequest(BaseModel):
    file_path: str = Field(..., description="Caminho para o arquivo .eml ou cabeçalho")


class MailAnalysisResponse(BaseModel):
    status: str
    data: Dict[str, Any]
