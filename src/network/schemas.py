from typing import Any, List, Optional

from pydantic import BaseModel, Field


class NetworkScanRequest(BaseModel):
    target: str = Field(..., examples=["192.168.1.1"], description="IP ou hostname do alvo")
    ports: Optional[list[int]] = Field(
        None, examples=[[22, 80, 443]], description="Lista de portas a escanear"
    )


class NetworkScanResponse(BaseModel):
    target: str
    status: str
    data: List[Any]
