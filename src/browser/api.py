from fastapi import APIRouter, HTTPException

from browser.browser_history import locale_database
from browser.schemas import BrowserHistoryRequest, BrowserHistoryResponse
from shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/browser", tags=["Browser"])


@router.post("/history", response_model=BrowserHistoryResponse)
def get_history(request: BrowserHistoryRequest):
    logger.info(
        "API /history chamada para navegador: %s com limite: %s", request.browser, request.limit
    )
    try:
        all_results = locale_database()

        filtered_data = []
        for res in all_results:
            if (
                not request.browser
                or request.browser.lower() == "all"
                or res.get("Navegador", "").lower() == request.browser.lower()
            ):
                filtered_data.extend(res.get("Dados", []))

        if request.limit:
            filtered_data = filtered_data[: request.limit]

        return BrowserHistoryResponse(status="success", data=filtered_data)
    except Exception as exc:
        logger.exception("Erro na extração de histórico.")
        raise HTTPException(status_code=500, detail=str(exc))
