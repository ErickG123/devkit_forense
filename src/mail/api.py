from fastapi import APIRouter

from mail.schemas import MailAnalysisRequest, MailAnalysisResponse
from shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/mail", tags=["Mail"])


@router.post("/analyze", response_model=MailAnalysisResponse)
def analyze_mail(request: MailAnalysisRequest):
    logger.info("API /analyze chamada para: %s", request.file_path)
    # Mock seguro simulando processamento
    result_data = {
        "headers": {"subject": "Mock Subject", "from": "test@example.com"},
        "body": "Mock body content",
    }
    return MailAnalysisResponse(status="success", data=result_data)
