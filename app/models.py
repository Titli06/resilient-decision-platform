from sqlalchemy import Column, Integer, String, JSON, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Request(Base):
    __tablename__ = "requests"
    id = Column(String, primary_key=True)
    workflow_id = Column(String, nullable=False)
    data = Column(JSON, nullable=False)
    status = Column(String, default="pending")  # pending, approved, rejected, manual_review
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String, nullable=False)
    stage = Column(String)
    rule = Column(Text)
    result = Column(String)
    explanation = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)