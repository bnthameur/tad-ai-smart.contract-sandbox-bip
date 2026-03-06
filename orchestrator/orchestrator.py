#!/usr/bin/env python3
"""
TAD AI - Orchestrator Module
Manages sub-agent workers for parallel task execution
"""

import sqlite3
import json
import time
import logging
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

# OpenClaw tools will be called via the tool system, not imported
# These are placeholder stubs that will be replaced with actual tool calls

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Orchestrator")

DB_PATH = Path(__file__).parent / "orchestrator.db"

class Worker:
    """Represents a sub-agent worker"""
    def __init__(self, worker_id: int, name: str, session_key: Optional[str] = None):
        self.id = worker_id
        self.name = name
        self.session_key = session_key
        self.status = "idle"
        self.task_description = ""
        self.progress = 0
        
class Orchestrator:
    """
    Main orchestrator that manages worker sub-agents.
    I use this to delegate tasks while staying responsive to user.
    """
    
    WORKER_NAMES = ["worker-alpha", "worker-beta", "worker-gamma"]
    
    def __init__(self):
        self._init_db()
        self.workers: Dict[str, Worker] = {}
        self._load_workers()
        
    def _init_db(self):
        """Initialize SQLite database"""
        DB_PATH.parent.mkdir(exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        with open(Path(__file__).parent / "schema.sql") as f:
            conn.executescript(f.read())
        conn.close()
        
    def _load_workers(self):
        """Load worker states from DB"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        for name in self.WORKER_NAMES:
            cursor.execute(
                "SELECT id, session_key, status FROM workers WHERE worker_name = ?",
                (name,)
            )
            row = cursor.fetchone()
            
            if row:
                self.workers[name] = Worker(row[0], name, row[1])
                self.workers[name].status = row[2]
            else:
                # Create new worker record
                cursor.execute(
                    "INSERT INTO workers (worker_name, status) VALUES (?, 'idle')",
                    (name,)
                )
                conn.commit()
                worker_id = cursor.lastrowid
                self.workers[name] = Worker(worker_id, name)
                
        conn.close()
        
    def get_available_worker(self) -> Optional[Worker]:
        """Find an idle worker or return None if all busy"""
        for name, worker in self.workers.items():
            if worker.status == "idle":
                return worker
        return None
        
    def spawn_worker(self, worker: Worker, task_type: str, description: str, 
                     project_path: str, task_details: str, session_key: str) -> bool:
        """
        Register a spawned worker (called by main agent after sessions_spawn).
        
        Args:
            session_key: The session key returned by sessions_spawn tool
        """
        try:
            worker.session_key = session_key
            worker.status = "running"
            worker.task_description = description
            worker.progress = 0
            
            # Update DB
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                """UPDATE workers 
                   SET session_key = ?, status = 'running', task_type = ?, 
                       task_description = ?, project_path = ?, started_at = ?,
                       progress = 0
                   WHERE id = ?""",
                (worker.session_key, task_type, description, project_path, 
                 datetime.now(), worker.id)
            )
            conn.commit()
            conn.close()
            
            logger.info(f"Registered {worker.name} with session {session_key[:20]}...")
            return True
            
        except Exception as e:
            logger.exception(f"Error registering worker: {e}")
            return False
            
    def get_status(self, worker_name: Optional[str] = None) -> Dict:
        """
        Get status of workers.
        I call this when you ask "what's the status?"
        """
        if worker_name and worker_name in self.workers:
            w = self.workers[worker_name]
            return {
                "name": w.name,
                "status": w.status,
                "task": w.task_description,
                "progress": w.progress
            }
        
        # Return all workers
        return {
            name: {
                "status": w.status,
                "task": w.task_description[:60] + "..." if len(w.task_description) > 60 else w.task_description,
                "progress": f"{w.progress}%"
            }
            for name, w in self.workers.items()
        }
        
    def update_worker_status(self, worker_name: str, session_response: Optional[str] = None):
        """Update worker status (called by main agent after checking sub-agent)"""
        if worker_name not in self.workers:
            return
            
        worker = self.workers[worker_name]
        
        # Parse progress from session response if provided
        if session_response:
            # Simple parsing - extract percentage if mentioned
            import re
            match = re.search(r'(\d+)%', session_response)
            if match:
                worker.progress = int(match.group(1))
            
            # Check if completed
            if "completed" in session_response.lower() or "done" in session_response.lower():
                worker.status = "completed"
                
            # Update DB
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "UPDATE workers SET progress = ?, status = ?, last_output = ? WHERE id = ?",
                (worker.progress, worker.status, session_response[-500:], worker.id)
            )
            conn.commit()
            conn.close
            
    def mark_worker_complete(self, worker_name: str, final_output: str = ""):
        """Mark worker as completed (called when sub-agent finishes)"""
        if worker_name not in self.workers:
            return
            
        worker = self.workers[worker_name]
        worker.status = "completed"
        worker.progress = 100
        
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """UPDATE workers 
               SET status = 'completed', progress = 100, completed_at = ?, last_output = ?
               WHERE id = ?""",
            (datetime.now(), final_output, worker.id)
        )
        conn.commit()
        conn.close()
            
    def cancel_worker(self, worker_name: str) -> bool:
        """
        Mark worker as cancelled.
        Note: Main agent should call sessions_send to actually stop the sub-agent.
        """
        if worker_name not in self.workers:
            return False
            
        worker = self.workers[worker_name]
        worker.status = "cancelled"
        
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "UPDATE workers SET status = 'cancelled', completed_at = ? WHERE id = ?",
                (datetime.now(), worker.id)
            )
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Error cancelling {worker_name}: {e}")
            return False
            
    def delegate_task(self, task_type: str, description: str, 
                      project_path: str) -> Optional[Worker]:
        """
        Get a worker ready for task assignment.
        
        Returns Worker object if available. 
        Main agent then calls sessions_spawn and registers the session key.
        
        Usage (from main agent):
            worker = orch.delegate_task('coding', 'Build UI', '/project')
            if worker:
                result = sessions_spawn(label=worker.name, task=..., mode='session')
                orch.spawn_worker(worker, 'coding', 'Build UI', '/project', result['sessionKey'])
        """
        worker = self.get_available_worker()
        
        if not worker:
            return None
            
        # Reserve the worker (will be confirmed when spawn_worker is called)
        worker.status = "reserved"
        worker.task_description = description
        
        return worker
            
    def get_summary(self) -> str:
        """Human-readable summary for user queries"""
        statuses = self.get_status()
        
        lines = ["📊 Worker Status:", ""]
        
        for name, info in statuses.items():
            emoji = "🟢" if info["status"] == "idle" else "🔴" if info["status"] == "running" else "⚪"
            lines.append(f"{emoji} {name}: {info['status'].upper()}")
            if info["task"]:
                lines.append(f"   └─ {info['task']}")
                lines.append(f"   └─ Progress: {info['progress']}")
        
        idle_count = sum(1 for s in statuses.values() if s["status"] == "idle")
        lines.append(f"\n✅ {idle_count}/3 workers available")
        
        return "\n".join(lines)

# Global orchestrator instance
_orchestrator: Optional[Orchestrator] = None

def get_orchestrator() -> Orchestrator:
    """Singleton accessor"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
