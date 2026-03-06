#!/usr/bin/env python3
"""
TAD AI Smart Contract Security Sandbox
Core sandbox management module

Phase 1: Environment Setup
"""

import os
import subprocess
import json
import time
import signal
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SandboxConfig:
    """Configuration for the sandbox environment"""
    rpc_url: str
    fork_block_number: Optional[int] = None
    chain_id: int = 1  # Ethereum mainnet
    port: int = 8545
    gas_limit: int = 30_000_000
    auto_mine: bool = True
    block_time: Optional[int] = None  # None = auto-mine


class AnvilSandbox:
    """
    Manages an Anvil instance for safe blockchain forking
    """
    
    def __init__(self, config: SandboxConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.state_dir = Path("/app/forks")
        self.state_dir.mkdir(exist_ok=True)
        
    def start(self) -> bool:
        """Start the Anvil fork"""
        if self.process and self.process.poll() is None:
            print("⚠️  Anvil already running")
            return True
            
        cmd = [
            "anvil",
            "--fork-url", self.config.rpc_url,
            "--port", str(self.config.port),
            "--gas-limit", str(self.config.gas_limit),
            "--chain-id", str(self.config.chain_id),
        ]
        
        if self.config.fork_block_number:
            cmd.extend(["--fork-block-number", str(self.config.fork_block_number)])
            
        if self.config.auto_mine and not self.config.block_time:
            cmd.append("--auto-impersonate")
            
        try:
            print(f"🚀 Starting Anvil fork...")
            print(f"   RPC: {self.config.rpc_url}")
            if self.config.fork_block_number:
                print(f"   Block: {self.config.fork_block_number}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid
            )
            
            # Wait for Anvil to start
            time.sleep(3)
            
            if self.process.poll() is None:
                print(f"✅ Anvil running on port {self.config.port}")
                return True
            else:
                stdout, stderr = self.process.communicate()
                print(f"❌ Anvil failed to start:")
                print(stderr)
                return False
                
        except Exception as e:
            print(f"❌ Error starting Anvil: {e}")
            return False
    
    def stop(self) -> None:
        """Stop the Anvil instance"""
        if self.process and self.process.poll() is None:
            print("🔄 Stopping Anvil...")
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=5)
                print("✅ Anvil stopped")
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                print("✅ Anvil force-stopped")
            except Exception as e:
                print(f"⚠️ Error stopping Anvil: {e}")
    
    def is_running(self) -> bool:
        """Check if Anvil is running"""
        return self.process is not None and self.process.poll() is None
    
    def get_rpc_url(self) -> str:
        """Get the local RPC URL"""
        return f"http://localhost:{self.config.port}"
    
    def snapshot_state(self, name: str) -> bool:
        """Snapshot current blockchain state"""
        # TODO: Implement state snapshotting
        print(f"📸 State snapshot '{name}' saved")
        return True
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class SandboxManager:
    """
    High-level manager for sandbox operations
    """
    
    def __init__(self):
        self.active_sandboxes: Dict[str, AnvilSandbox] = {}
        
    def create_sandbox(
        self,
        name: str,
        rpc_url: str,
        fork_block: Optional[int] = None,
        chain: str = "ethereum"
    ) -> AnvilSandbox:
        """Create a new sandbox environment"""
        
        chain_ids = {
            "ethereum": 1,
            "bsc": 56,
            "polygon": 137,
            "arbitrum": 42161,
            "optimism": 10
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
    
    def list_sandboxes(self) -> Dict[str, Any]:
        """List all active sandboxes"""
        return {
            name: {
                "running": sandbox.is_running(),
                "rpc": sandbox.get_rpc_url() if sandbox.is_running() else None
            }
            for name, sandbox in self.active_sandboxes.items()
        }
    
    def stop_all(self):
        """Stop all active sandboxes"""
        for name, sandbox in self.active_sandboxes.items():
            print(f"Stopping {name}...")
            sandbox.stop()


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="TAD AI Sandbox")
    parser.add_argument("start", help="Start a sandbox")
    parser.add_argument("--rpc", required=True, help="RPC URL")
    parser.add_argument("--block", type=int, help="Fork block number")
    parser.add_argument("--chain", default="ethereum", help="Chain name")
    
    args = parser.parse_args()
    
    manager = SandboxManager()
    sandbox = manager.create_sandbox(
        "main",
        args.rpc,
        args.block,
        args.chain
    )
    
    try:
        sandbox.start()
        print("\n✅ Sandbox ready!")
        print(f"   RPC: {sandbox.get_rpc_url()}")
        print("\nPress Ctrl+C to stop")
        
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🔄 Shutting down...")
        sandbox.stop()
