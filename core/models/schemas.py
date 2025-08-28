from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

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
    execution_id: str

class Result(ResultBase):
    id: str
    created_at: datetime

    class Config:
        orm_mode = True

class ExecutionBase(BaseModel):
    network: str
    cli_version: Optional[str] = None

class ExecutionCreateSchema(ExecutionBase):
    func_id: str
    data: Optional[Any] = None

class ExecutionSchema(ExecutionBase):
    id: str
    functionality_id: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    result: Optional[Result] = None

    class Config:
        orm_mode = True

class FunctionalityBase(BaseModel):
    name: str
    description: Optional[str]

class FunctionalityCreate(FunctionalityBase):
    module_id: str

class Functionality(FunctionalityBase):
    id: str
    executions: List[ExecutionSchema] = []

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
