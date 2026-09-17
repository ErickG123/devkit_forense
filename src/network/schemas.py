"""
Schemas Pydantic e Camada Anti-Corrupção (ACL) para a feature Network.

Garante que mudanças estruturais ou acréscimo de campos no motor Go não quebrem
os contratos da API FastAPI nem os comandos Typer.
"""

from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class NetworkScanRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    target: str = Field(..., examples=["192.168.1.1"], description="IP ou hostname do alvo")
    ports: Optional[List[int]] = Field(
        None, examples=[[22, 80, 443]], description="Lista de portas a escanear"
    )


class OpenPortDTO(BaseModel):
    """Representa a porta aberta validada pela ACL."""
    model_config = ConfigDict(extra="ignore")

    port: int = Field(..., ge=1, le=65535, description="Número da porta TCP")
    protocol: str = Field("tcp", description="Protocolo da camada de transporte")
    state: str = Field("open", description="Estado da porta")
    service: str = Field("unknown", description="Nome do serviço identificado")
    banner: Optional[str] = Field(None, description="Banner bruto ou assinatura de serviço capturada")
    latency_ms: int = Field(0, ge=0, description="Latência de conexão em milissegundos")


class NetworkScanDataDTO(BaseModel):
    """Payload de dados brutos retornados pelo Go Core."""
    model_config = ConfigDict(extra="ignore")

    target: str
    scanned_ports: int = Field(0, ge=0)
    open_ports: List[OpenPortDTO] = Field(default_factory=list)
    total_open: int = Field(0, ge=0)


class NetworkScanResponse(BaseModel):
    """Contrato final para APIs e consumidores externos."""
    model_config = ConfigDict(extra="ignore")

    target: str
    status: str
    data: List[Any]
