from fastapi import APIRouter

from browser.schemas import BrowserHistoryRequest, BrowserHistoryResponse
from shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/browser", tags=["Browser"])


@router.post("/history", response_model=BrowserHistoryResponse)
def get_history(request: BrowserHistoryRequest):
    logger.info(
        "API /history chamada para navegador: %s com limite: %s", request.browser, request.limit
    )
    # Mock seguro simulando processamento
    result_data = [
        {"url": "https://example.com", "title": "Example", "visit_count": 10},
        {"url": "https://google.com", "title": "Google", "visit_count": 5},
    ]
    if request.limit:
        result_data = result_data[: request.limit]
    return BrowserHistoryResponse(status="success", data=result_data)
