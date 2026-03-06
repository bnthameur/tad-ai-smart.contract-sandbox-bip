#!/usr/bin/env python3
"""
TAD AI Smart Contract Security Sandbox
Core sandbox management module
Production-Ready Version
"""

import os
import subprocess
import signal
import time
import shutil
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SandboxManager")

@dataclass
class SandboxConfig:
    """Configuration for the sandbox environment"""
    rpc_url: str
    fork_block_number: Optional[int] = None
    chain_id: int = 1
    port: int = 8545
    gas_limit: int = 30_000_000
    auto_mine: bool = True
    block_time: Optional[int] = None

class AnvilSandbox:
    """
    Manages an Anvil instance for safe blockchain forking.
    Handles process lifecycles and cleanup robustly.
    """
    
    def __init__(self, config: SandboxConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        # Use relative path for portability
        self.state_dir = Path("forks")
        self.state_dir.mkdir(exist_ok=True, parents=True)
        
    def _find_anvil(self) -> str:
        """Locate the anvil binary"""
        # Check PATH first
        anvil_path = shutil.which("anvil")
        if anvil_path:
            return anvil_path
            
        # Check common locations
        home = Path.home()
        common_paths = [
            home / ".foundry/bin/anvil",
            Path("/root/.foundry/bin/anvil"),
            Path("/usr/local/bin/anvil")
        ]
        
        for path in common_paths:
            if path.exists():
                return str(path)
                
        raise FileNotFoundError("Anvil binary not found. Please install Foundry.")

    def start(self) -> bool:
        """Start the Anvil fork"""
        if self.is_running():
            logger.info("Anvil already running")
            return True
            
        try:
            anvil_bin = self._find_anvil()
            
            cmd = [
                anvil_bin,
                "--port", str(self.config.port),
                "--gas-limit", str(self.config.gas_limit),
                "--chain-id", str(self.config.chain_id),
            ]
            
            if self.config.rpc_url:
                cmd.extend(["--fork-url", self.config.rpc_url])
                
            if self.config.fork_block_number:
                cmd.extend(["--fork-block-number", str(self.config.fork_block_number)])
            
            if self.config.auto_mine and not self.config.block_time:
                cmd.append("--auto-impersonate")
            
            logger.info(f"🚀 Starting Anvil on port {self.config.port}...")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid
            )
            
            # Health check loop
            for _ in range(10):
                time.sleep(0.5)
                if self.process.poll() is not None:
                    # Process died
                    _, stderr = self.process.communicate()
                    logger.error(f"Anvil failed to start: {stderr}")
                    return False
                
                # In production, we might check if port is listening here
                # For now, if it hasn't died in 2s, we assume it's good
                
            logger.info("✅ Anvil started successfully")
            return True
                
        except Exception as e:
            logger.exception(f"Error starting Anvil: {e}")
            return False
    
    def stop(self) -> None:
        """Stop the Anvil instance safely"""
        if self.process:
            logger.info("🔄 Stopping Anvil...")
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=5)
                logger.info("✅ Anvil stopped")
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                logger.warning("⚠️ Anvil force-stopped")
            except Exception as e:
                logger.error(f"Error stopping Anvil: {e}")
            finally:
                self.process = None
    
    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None
    
    def get_rpc_url(self) -> str:
        return f"http://localhost:{self.config.port}"

class SandboxManager:
    """High-level manager for sandbox operations"""
    
    def __init__(self):
        self.active_sandboxes: Dict[str, AnvilSandbox] = {}
        
    def create_sandbox(
        self,
        name: str,
        rpc_url: str,
        fork_block: Optional[int] = None,
        chain: str = "ethereum"
    ) -> AnvilSandbox:
        chain_ids = {
            "ethereum": 1, "bsc": 56, "polygon": 137, 
            "arbitrum": 42161, "optimism": 10
        }
        
        config = SandboxConfig(
            rpc_url=rpc_url,
            fork_block_number=fork_block,
            chain_id=chain_ids.get(chain, 1),
            port=8545 + len(self.active_sandboxes)
        )
        
        sandbox = AnvilSandbox(config)
        self.active_sandboxes[name] = sandbox
        return sandbox
    
    def stop_all(self):
        for name, sandbox in self.active_sandboxes.items():
            sandbox.stop()
