import os

from fastapi import APIRouter, HTTPException

from mail.email_parser import parse_eml_file
from mail.schemas import MailAnalysisRequest, MailAnalysisResponse
from shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/mail", tags=["Mail"])


@router.post("/analyze", response_model=MailAnalysisResponse)
def analyze_mail(request: MailAnalysisRequest):
    logger.info("API /analyze chamada para: %s", request.file_path)
    try:
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
        result_data = parse_eml_file(request.file_path)
        return MailAnalysisResponse(status="success", data=result_data)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Erro ao processar arquivo .eml.")
        raise HTTPException(status_code=500, detail=str(exc))
