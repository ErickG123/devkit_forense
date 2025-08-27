import core.models.orm as orm
import core.models.schemas as schemas
from api.utils.db import get_db

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/modules", tags=["Modules"])

@router.post("/", response_model=schemas.Module)
def create_module(module: schemas.ModuleCreate, db: Session = Depends(get_db)):
    db_module = orm.Module(name=module.name, description=module.description)
    db.add(db_module)
    db.commit()
    db.refresh(db_module)
    return db_module

@router.get("/", response_model=List[schemas.Module])
def get_modules(db: Session = Depends(get_db)):
    return db.query(orm.Module).all()
