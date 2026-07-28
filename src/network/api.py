"""
API Router da feature Network.

Expõe endpoints REST para as operações de rede do ForenseLab.
Consome diretamente as funções do pacote `network.*`, que retornam
dicionários limpos — sem efeitos colaterais de I/O.
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from network.dns_recon import dns_recon
from network.ip_info import ip_info_lookup
from network.ping_sweep import parse_network, ping_host
from network.port_scanner import scan_host
from network.schemas import NetworkScanRequest, NetworkScanResponse
from network.traceroute import traceroute_host
from shared.config import get as cfg_get
from shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/network", tags=["Network"])

_DEFAULT_PORTS = cfg_get("network", "default_ports", default="21,22,53,80,443,445,3306,8080")


# ---------------------------------------------------------------------------
# Modelos Pydantic (contratos de entrada)
# ---------------------------------------------------------------------------


class SweepRequest(BaseModel):
    network: str = Field(
        ..., examples=["192.168.1.1-254"], description="Range de IPs. Ex: 192.168.1.1-254"
    )


class DnsRequest(BaseModel):
    targets: list[str] = Field(
        ..., examples=[["google.com"]], description="Lista de domínios ou IPs para consulta"
    )
    with_subdomains: bool = Field(False, description="Tentar descobrir subdomínios comuns")


class TracerouteRequest(BaseModel):
    host: str = Field(..., examples=["google.com"], description="Domínio ou IP de destino")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/scan",
    summary="Port Scan",
    description="Realiza um scan de portas TCP em um host e retorna as portas abertas com serviços e banners.",
    response_model=NetworkScanResponse,
)
def run_port_scan(request: NetworkScanRequest):
    logger.info("API /scan — alvo: %s | portas (list): %s", request.target, request.ports)
    try:
        ports_str = ",".join(map(str, request.ports)) if request.ports else _DEFAULT_PORTS
        results = scan_host(target=request.target, ports=ports_str)
        logger.info("API /scan concluído — %d resultado(s).", len(results))
        return NetworkScanResponse(target=request.target, status="success", data=results)
    except Exception as exc:
        logger.exception("Erro em /scan para '%s'.", request.target)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/sweep",
    summary="Ping Sweep",
    description="Verifica quais hosts estão ativos em um range de IPs via ICMP ping.",
)
def run_ping_sweep(request: SweepRequest):
    logger.info("API /sweep — range: %s", request.network)
    try:
        ips = parse_network(request.network)
        alive = [ip for ip in ips if ping_host(ip)]
        return {"network": request.network, "status": "success", "alive_hosts": alive}
    except Exception as exc:
        logger.exception("Erro em /sweep para '%s'.", request.network)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/dns",
    summary="DNS Recon",
    description="Realiza reconhecimento DNS em um ou mais domínios/IPs.",
)
def run_dns_recon(request: DnsRequest):
    logger.info("API /dns — targets: %s", request.targets)
    try:
        results = dns_recon(request.targets, with_subdomains=request.with_subdomains)
        return {"status": "success", "data": results}
    except Exception as exc:
        logger.exception("Erro em /dns.")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/ipinfo",
    summary="IP Info",
    description="Retorna informações de geolocalização e ASN para um IP ou hostname.",
)
def run_ip_info(
    ip: Annotated[str, Query(description="IP ou hostname. Ex: 8.8.8.8")],
):
    logger.info("API /ipinfo — ip: %s", ip)
    try:
        result = ip_info_lookup(ip)
        return {"ip": ip, "status": "success", "data": result}
    except Exception as exc:
        logger.exception("Erro em /ipinfo para '%s'.", ip)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/traceroute",
    summary="Traceroute",
    description="Executa um traceroute até o host e retorna os hops com RTT.",
)
def run_traceroute(request: TracerouteRequest):
    logger.info("API /traceroute — host: %s", request.host)
    try:
        hops = traceroute_host(request.host)
        return {"host": request.host, "status": "success", "hops": hops}
    except Exception as exc:
        logger.exception("Erro em /traceroute para '%s'.", request.host)
        raise HTTPException(status_code=500, detail=str(exc))
