from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    api_key = Column(String, unique=True, index=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    projects = relationship("Project", back_populates="owner")
    scans = relationship("Scan", back_populates="user")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    owner = relationship("User", back_populates="projects")
    scans = relationship("Scan", back_populates="project")

class Scan(Base):
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Target info
    contract_address = Column(String)
    chain = Column(String)
    contract_source = Column(Text)
    
    # AI Configuration
    model_provider = Column(String)  # deepseek, openai, etc.
    
    # Status tracking
    status = Column(String, default="pending")  # pending, analyzing, exploiting, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    
    # Results
    vulnerabilities_found = Column(Integer, default=0)
    exploit_successful = Column(Integer, default=0)
    profit_estimate_usd = Column(Float, default=0.0)
    total_cost_usd = Column(Float, default=0.0)
    execution_time_seconds = Column(Float, default=0.0)
    
    # Full report stored as JSON
    full_report = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    project = relationship("Project", back_populates="scans")
    user = relationship("User", back_populates="scans")
    vulnerabilities = relationship("Vulnerability", back_populates="scan")

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    
    name = Column(String)
    severity = Column(String)  # CRITICAL, HIGH, MEDIUM, LOW
    description = Column(Text)
    impact = Column(Text)
    exploit_scenario = Column(Text)
    exploit_code = Column(Text)
    suggested_fix = Column(Text)
    
    scan = relationship("Scan", back_populates="vulnerabilities")
