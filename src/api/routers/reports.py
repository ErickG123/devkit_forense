from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import shared.orm as orm
import shared.schemas as schemas
from api.utils.db import get_db

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
