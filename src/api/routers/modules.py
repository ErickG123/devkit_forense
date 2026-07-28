from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import shared.orm as orm
import shared.schemas as schemas
from api.utils.db import get_db

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
