from pydantic import BaseModel
from typing import List, Optional

class ReportBase(BaseModel):
    file_path: str

class ReportCreate(ReportBase):
    result_id: str

class Report(ReportBase):
    id: str
    created_at: str

    class Config:
        orm_mode = True

class ResultBase(BaseModel):
    data: str

class ResultCreate(ResultBase):
    functionality_id: str

class Result(ResultBase):
    id: str
    created_at: str

    class Config:
        orm_mode = True

class FunctionalityBase(BaseModel):
    name: str
    description: Optional[str]

class FunctionalityCreate(FunctionalityBase):
    module_id: str

class Functionality(FunctionalityBase):
    id: str
    results: List[Result] = []

    class Config:
        orm_mode = True

class ModuleBase(BaseModel):
    name: str
    description: Optional[str]

class ModuleCreate(ModuleBase):
    pass

class Module(ModuleBase):
    id: str
    functionalities: List[Functionality] = []

    class Config:
        orm_mode = True
