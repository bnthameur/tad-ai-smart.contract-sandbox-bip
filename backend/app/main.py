from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
import os

from app.db.session import get_db, engine
from app.models import models
from app.schemas import schemas
from app.workers.celery_worker import run_security_scan, celery_app

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TAD AI Sandbox API",
    description="AI-Powered Smart Contract Security Platform",
    version="2.0.0"
)

security = HTTPBearer()

# Simple API key auth (for MVP)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    api_key = credentials.credentials
    user = db.query(models.User).filter(models.User.api_key == api_key).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user

@app.post("/auth/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register new user"""
    import secrets
    import hashlib
    
    # Check if exists
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    db_user = models.User(
        email=user.email,
        hashed_password=hashlib.sha256(user.password.encode()).hexdigest(),  # Simple hash for MVP
        api_key=secrets.token_urlsafe(32)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/projects", response_model=schemas.ProjectResponse)
def create_project(project: schemas.ProjectCreate, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create new project"""
    db_project = models.Project(**project.dict(), owner_id=user.id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/projects", response_model=List[schemas.ProjectResponse])
def list_projects(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List user's projects"""
    return db.query(models.Project).filter(models.Project.owner_id == user.id).all()

@app.post("/scans", response_model=schemas.ScanResponse)
def create_scan(scan: schemas.ScanCreate, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Start new security scan"""
    # Verify project ownership
    project = db.query(models.Project).filter(
        models.Project.id == scan.project_id,
        models.Project.owner_id == user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create scan record
    db_scan = models.Scan(
        **scan.dict(),
        user_id=user.id,
        status="pending",
        progress=0
    )
    db.add(db_scan)
    db.commit()
    db.refresh(db_scan)
    
    # Queue background task
    run_security_scan.delay(
        scan_id=db_scan.id,
        contract_address=scan.contract_address,
        chain=scan.chain,
        contract_source=scan.contract_source,
        model_provider=scan.model_provider
    )
    
    return db_scan

@app.get("/scans/{scan_id}", response_model=schemas.ScanDetailResponse)
def get_scan(scan_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get scan details and results"""
    scan = db.query(models.Scan).filter(
        models.Scan.id == scan_id,
        models.Scan.user_id == user.id
    ).first()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return scan

@app.get("/scans", response_model=List[schemas.ScanResponse])
def list_scans(project_id: int = None, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List user's scans"""
    query = db.query(models.Scan).filter(models.Scan.user_id == user.id)
    if project_id:
        query = query.filter(models.Scan.project_id == project_id)
    return query.order_by(models.Scan.created_at.desc()).all()

@app.websocket("/ws/scans/{scan_id}")
async def scan_websocket(websocket: WebSocket, scan_id: int):
    """WebSocket for real-time scan progress"""
    await websocket.accept()
    
    # Poll Celery task status and stream to client
    # Implementation simplified for MVP
    await websocket.send_json({"status": "connected", "scan_id": scan_id})
    
    # In production: subscribe to Redis pub/sub for real-time updates
    while True:
        # Check task status
        task = celery_app.AsyncResult(f"scan_{scan_id}")
        if task.state == "PROGRESS":
            await websocket.send_json(task.info)
        elif task.state in ["SUCCESS", "FAILURE"]:
            await websocket.send_json({"status": task.state, "result": task.result if task.state == "SUCCESS" else task.info})
            break
        await asyncio.sleep(1)

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}
