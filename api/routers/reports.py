import core.models.orm as orm
import core.models.schemas as schemas
from api.utils.db import get_db

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/reports/", response_model=schemas.Report)
def create_report(report: schemas.ReportCreate, db: Session = Depends(get_db)):
    db_report = orm.Report(result_id=report.result_id, file_path=report.file_path)
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

@router.get("/reports/", response_model=List[schemas.Report])
def get_reports(db: Session = Depends(get_db)):
    return db.query(orm.Report).all()
