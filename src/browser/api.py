"""
API Router da feature Browser.

Expõe endpoints REST para extração de artefatos de navegadores.
Os endpoints de extração são operações de longa duração — em produção
considere movê-los para tarefas assíncronas (ex: Celery/BackgroundTasks).
"""

from fastapi import APIRouter

from shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Health-check da feature
# ---------------------------------------------------------------------------


@router.get(
    "/health",
    summary="Browser Feature Health-check",
    description="Confirma que o módulo de análise de navegadores está disponível.",
)
def browser_health():
    return {
        "feature": "browser",
        "status": "online",
        "endpoints_available": [
            "GET  /browser/health",
        ],
        "note": (
            "Os endpoints de extração (history, downloads, logins) operam sobre "
            "o sistema de arquivos local e serão expostos em versões futuras da API."
        ),
    }
