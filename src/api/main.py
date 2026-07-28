from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import network

app = FastAPI(
    title="ForenseLab API",
    description="API REST do DevKit Forense para análise de evidências digitais.",
    version="1.0.0",
)

# Configuração de CORS para permitir consumo pelo Dashboard SPA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restringir para o domínio da Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro dos Roteadores baseados em features
app.include_router(network.router, prefix="/api/network", tags=["Network"])
# app.include_router(browser.router, prefix="/api/browser", tags=["Browser"])
# app.include_router(email.router, prefix="/api/email", tags=["Email"])


@app.get("/")
def root():
    return {"message": "ForenseLab API está online e operante!"}
