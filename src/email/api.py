"""
API Router da feature Email.

Expõe endpoints REST para análise forense de e-mails.
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
    summary="Email Feature Health-check",
    description="Confirma que o módulo de análise de e-mails está disponível.",
)
def email_health():
    return {
        "feature": "email",
        "status": "online",
        "endpoints_available": [
            "GET  /email/health",
        ],
        "note": (
            "Os endpoints de parsing (.eml) e análise de cabeçalhos serão "
            "expostos em versões futuras da API REST."
        ),
    }
