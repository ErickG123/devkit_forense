from core.db.db import engine, Base
from api.routers import modules, functionalities, results, reports, executions

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DevKit Forense API")

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(modules.router)
app.include_router(functionalities.router)
app.include_router(results.router)
app.include_router(reports.router)
app.include_router(executions.router)
