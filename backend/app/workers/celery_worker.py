from celery import Celery
import os
import sys
from pathlib import Path

# Add parent directory to import core modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import our core simulation engine
from src.simulation import SimulationEngine
from src.agent import create_agent

# Celery app configuration
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery(
    "tad_sandbox",
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(
    bind=True,
    max_retries=3,  # Retry failed tasks 3 times
    default_retry_delay=60,  # Wait 1 min between retries
    autoretry_for=(Exception,),  # Retry on any error
    retry_backoff=True  # Exponential backoff
)
def run_security_scan(self, scan_id: int, contract_address: str, chain: str, 
                      contract_source: Optional[str], model_provider: str):
    """
    Background task to run security analysis
    Updates progress via self.update_state()
    """
    from app.db.session import SessionLocal
    from app.models.models import Scan, Vulnerability
    
    db = SessionLocal()
    
    try:
        # Get scan record
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return {"error": "Scan not found"}
        
        # Update status
        scan.status = "analyzing"
        scan.progress = 10
        db.commit()
        
        # Update Celery state for real-time progress
        self.update_state(
            state="PROGRESS",
            meta={"progress": 10, "status": "Initializing AI Agent..."}
        )
        
        # Run the simulation
        rpc_url = os.getenv("RPC_URL_MAINNET")
        engine = SimulationEngine(
            model_provider=model_provider,
            rpc_url=rpc_url
        )
        
        scan.progress = 30
        self.update_state(state="PROGRESS", meta={"progress": 30, "status": "Forking blockchain..."})
        
        result = engine.run_simulation(
            address=contract_address,
            chain=chain
        )
        
        scan.progress = 80
        self.update_state(state="PROGRESS", meta={"progress": 80, "status": "Processing results..."})
        
        # Update scan with results
        scan.status = "completed"
        scan.progress = 100
        scan.vulnerabilities_found = len(result.vulnerabilities)
        scan.exploit_successful = 1 if result.exploit_successful else 0
        scan.profit_estimate_usd = result.net_profit_usd
        scan.total_cost_usd = result.cost
        scan.execution_time_seconds = result.execution_time
        scan.full_report = {
            "vulnerabilities": result.vulnerabilities,
            "exploit_code": result.exploit_code,
            "raw_response": result.raw_response
        }
        
        # Save individual vulnerabilities
        for vuln_data in result.vulnerabilities:
            vuln = Vulnerability(
                scan_id=scan_id,
                name=vuln_data.get("name", "Unknown"),
                severity=vuln_data.get("severity", "MEDIUM"),
                description=vuln_data.get("description", ""),
                impact=vuln_data.get("impact", ""),
                exploit_scenario=vuln_data.get("exploit_scenario", ""),
                exploit_code=result.exploit_code,
                suggested_fix=vuln_data.get("suggested_fix", "")
            )
            db.add(vuln)
        
        db.commit()
        
        return {
            "scan_id": scan_id,
            "status": "completed",
            "vulnerabilities_found": scan.vulnerabilities_found,
            "cost_usd": scan.total_cost_usd
        }
        
    except Exception as e:
        scan.status = "failed"
        db.commit()
        self.update_state(state="FAILURE", meta={"error": str(e)})
        # Retry the task
        try:
            self.retry(countdown=60)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for scan {scan_id}")
            # Final failure - could send alert here
        raise
        
    finally:
        db.close()
