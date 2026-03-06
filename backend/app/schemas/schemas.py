from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# User schemas
class UserCreate(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    api_key: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Project schemas
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Scan schemas
class ScanCreate(BaseModel):
    project_id: int
    contract_address: str
    chain: str = "ethereum"
    contract_source: Optional[str] = None
    model_provider: str = "deepseek"

class ScanResponse(BaseModel):
    id: int
    project_id: int
    status: str
    progress: int
    contract_address: str
    chain: str
    model_provider: str
    vulnerabilities_found: int
    exploit_successful: int
    profit_estimate_usd: float
    total_cost_usd: float
    execution_time_seconds: float
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ScanDetailResponse(ScanResponse):
    full_report: Optional[dict] = None
    vulnerabilities: List[dict] = []

# Vulnerability schemas
class VulnerabilityResponse(BaseModel):
    id: int
    scan_id: int
    name: str
    severity: str
    description: str
    impact: str
    exploit_code: Optional[str]
    suggested_fix: Optional[str]
    
    class Config:
        from_attributes = True

# Real-time progress
class ScanProgress(BaseModel):
    scan_id: int
    status: str
    progress: int
    message: str
    timestamp: datetime
