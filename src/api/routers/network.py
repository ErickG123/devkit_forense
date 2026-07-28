from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from network.port_scanner import scan_host

router = APIRouter()


class ScanRequest(BaseModel):
    target: str
    ports: str = "21,22,80,443,8080"


@router.post("/scan")
def run_port_scan(request: ScanRequest):
    try:
        # A chamada ao Core que agora retorna um dicionário limpo
        results = scan_host(target=request.target, ports=request.ports)
        return {"target": request.target, "status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
