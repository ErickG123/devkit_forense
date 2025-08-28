from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from core.db.db import Base

class Module(Base):
    __tablename__ = "modules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    functionalities = relationship("Functionality", back_populates="module")

class Functionality(Base):
    __tablename__ = "functionalities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    module_id = Column(String, ForeignKey("modules.id"))
    name = Column(String)
    description = Column(Text)

    module = relationship("Module", back_populates="functionalities")
    executions = relationship("Execution", back_populates="functionality")

class Execution(Base):
    __tablename__ = "executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    functionality_id = Column(String, ForeignKey("functionalities.id"))
    network = Column(String, nullable=False)
    status = Column(String, default="started")
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    cli_version = Column(String, nullable=True)

    functionality = relationship("Functionality", back_populates="executions")
    result = relationship("Result", back_populates="execution", uselist=False)

class Result(Base):
    __tablename__ = "results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id = Column(String, ForeignKey("executions.id"))
    data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    execution = relationship("Execution", back_populates="result")
