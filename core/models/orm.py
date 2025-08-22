from sqlalchemy import Column, String, Text, ForeignKey, DateTime
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
    results = relationship("Result", back_populates="functionality")

class Result(Base):
    __tablename__ = "results"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    functionality_id = Column(String, ForeignKey("functionalities.id"))
    data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    functionality = relationship("Functionality", back_populates="results")

class Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    result_id = Column(String, ForeignKey("results.id"))
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
