import core.models.orm as orm
import core.models.schemas as schemas
from core.db.db import SessionLocal
from api.utils.db import get_db

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import sys

CLI_PYTHON = sys.executable

router = APIRouter(prefix="/functionalities", tags=["Functionalities"])

@router.post("/functionalities/", response_model=schemas.Functionality)
def create_functionality(functionality: schemas.FunctionalityCreate, db: Session = Depends(get_db)):
    db_func = orm.Functionality(
        name=functionality.name,
        description=functionality.description,
        module_id=functionality.module_id
    )
    db.add(db_func)
    db.commit()
    db.refresh(db_func)
    return db_func

@router.get("/functionalities/", response_model=List[schemas.Functionality])
def get_functionalities(db: Session = Depends(get_db)):
    return db.query(orm.Functionality).all()

@router.get("/functionalities/{func_id}/results", response_model=List[schemas.Result])
def get_results_by_functionality(func_id: str, db: Session = Depends(get_db)):
    return db.query(orm.Result).filter(orm.Result.functionality_id == func_id).all()

@router.post("/functionalities/{func_id}/run")
def run_functionality(func_id: str, network: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    func = db.query(orm.Functionality).filter(orm.Functionality.id == func_id).first()
    if not func:
        raise HTTPException(status_code=404, detail="Funcionalidade não encontrada")

    module_name = func.module.name
    func_name = func.name
    func_id_db = func.id

    def execute_cli():
        try:
            import subprocess
            import os
            from pathlib import Path

            CLI_BASE_DIR = Path(__file__).parent.parent

            python_module_path = f"core.{module_name}.{func_name}"
            output_dir = CLI_BASE_DIR / "cli_output"
            os.makedirs(output_dir, exist_ok=True)

            subprocess.run(
                [
                    CLI_PYTHON,
                    "-m", python_module_path,
                    "--network", network,
                    "--output-dir", str(output_dir)
                ],
                check=True,
                cwd=CLI_BASE_DIR
            )

            output_file = output_dir / f"{func_name}.json"
            if output_file.exists():
                with open(output_file, "r", encoding="utf-8") as f:
                    data = f.read()

                db_session = SessionLocal()
                result = orm.Result(functionality_id=func_id_db, data=data)
                db_session.add(result)
                db_session.commit()
                db_session.refresh(result)
                db_session.close()

        except subprocess.CalledProcessError as e:
            print(f"Erro ao executar CLI: {e}")
        except Exception as e:
            print(f"Erro ao processar resultados: {e}")

    background_tasks.add_task(execute_cli)

    return {"status": "execução iniciada em background", "funcionalidade": func_name}
