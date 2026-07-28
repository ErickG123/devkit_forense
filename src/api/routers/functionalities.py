import json
import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

import shared.orm as orm
import shared.schemas as schemas
from api.utils.db import get_db
from shared.db import SessionLocal
from shared.registry import FUNCTIONALITIES

router = APIRouter(prefix="/functionalities", tags=["Functionalities"])


@router.post("/", response_model=schemas.Functionality)
def create_functionality(functionality: schemas.FunctionalityCreate, db: Session = Depends(get_db)):
    db_func = orm.Functionality(
        name=functionality.name,
        description=functionality.description,
        module_id=functionality.module_id,
    )
    db.add(db_func)
    db.commit()
    db.refresh(db_func)
    return db_func


@router.get("/", response_model=list[schemas.Functionality])
def get_functionalities(db: Session = Depends(get_db)):
    return db.query(orm.Functionality).all()


@router.get("/{func_id}/results", response_model=list[schemas.Result])
def get_results_by_functionality(func_id: str, db: Session = Depends(get_db)):
    executions = db.query(orm.Execution).filter(orm.Execution.functionality_id == func_id).all()
    results = []
    for exe in executions:
        if exe.result:
            results.append(exe.result)
    return results


@router.post("/{func_id}/run")
def run_functionality(
    func_id: str,
    network: str = None,
    background_tasks: BackgroundTasks = None,
    usuario: str = "Usuário Anônimo",
    db: Session = Depends(get_db),
):
    func_obj = db.query(orm.Functionality).filter(orm.Functionality.id == func_id).first()
    if not func_obj:
        raise HTTPException(status_code=404, detail="Funcionalidade não encontrada")

    func_name = func_obj.name
    if func_name not in FUNCTIONALITIES:
        raise HTTPException(status_code=400, detail=f"Funcionalidade '{func_name}' não registrada")

    def execute_core():
        try:
            output_dir = Path(__file__).parent.parent / "cli_output"
            os.makedirs(output_dir, exist_ok=True)

            func = FUNCTIONALITIES[func_name]

            if func_name == "network_map":
                result_data = func(network, str(output_dir))
            else:
                result_data = func(usuario=usuario, output_dir=str(output_dir))

            db_session = SessionLocal()
            execution = orm.Execution(
                functionality_id=func_obj.id,
                network=network or "N/A",
                status="started",
                started_at=datetime.utcnow(),
            )
            db_session.add(execution)
            db_session.commit()
            db_session.refresh(execution)

            result = orm.Result(
                execution_id=execution.id,
                data=json.dumps(result_data, ensure_ascii=False),
                created_at=datetime.utcnow(),
            )
            db_session.add(result)
            db_session.commit()
            db_session.refresh(result)
            db_session.close()

            print(f"✅ {func_name} executado com sucesso!")

        except Exception as e:
            print(f"❌ Erro ao executar {func_name}: {e}")

    background_tasks.add_task(execute_core)
    return {"status": "execução iniciada em background", "funcionalidade": func_name}
