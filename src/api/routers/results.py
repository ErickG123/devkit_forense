import core.models.orm as orm
import core.models.schemas as schemas
from api.utils.db import get_db

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/results", tags=["Results"])

@router.post("/results/", response_model=schemas.Result)
def create_result(result: schemas.ResultCreate, db: Session = Depends(get_db)):
    db_result = orm.Result(
        functionality_id=result.functionality_id,
        data=result.data
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

@router.get("/results/", response_model=List[schemas.Result])
def get_results(db: Session = Depends(get_db)):
    return db.query(orm.Result).all()

@router.get("/results/{result_id}/reports", response_model=List[schemas.Report])
def get_reports_by_result(result_id: str, db: Session = Depends(get_db)):
    return db.query(orm.Report).filter(orm.Report.result_id == result_id).all()
