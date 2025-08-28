from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from api.utils.db import get_db
import core.models.orm as orm
from core.models.schemas import ExecutionCreateSchema, ExecutionSchema
from datetime import datetime

router = APIRouter(prefix="/executions", tags=["Executions"])

@router.post("/start", response_model=ExecutionSchema)
def start_execution(payload: ExecutionCreateSchema, db: Session = Depends(get_db)):
    func = db.query(orm.Functionality).filter(orm.Functionality.id == payload.func_id).first()
    if not func:
        raise HTTPException(status_code=404, detail="Funcionalidade não encontrada")

    execution = orm.Execution(
        functionality_id=func.id,
        network=payload.network,
        status="started",
        cli_version=payload.cli_version
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    return execution

@router.post("/finish", response_model=ExecutionSchema)
def finish_execution(payload: ExecutionCreateSchema, db: Session = Depends(get_db)):
    execution = db.query(orm.Execution).filter(
        orm.Execution.functionality_id == payload.func_id,
        orm.Execution.network == payload.network,
        orm.Execution.status == "started"
    ).first()

    if not execution:
        raise HTTPException(status_code=404, detail="Execução não encontrada")

    execution.status = "finished"
    execution.finished_at = datetime.utcnow()
    execution.cli_version = payload.cli_version

    result = orm.Result(execution_id=execution.id, data=payload.data)
    db.add(result)
    db.commit()
    db.refresh(execution)

    return execution
