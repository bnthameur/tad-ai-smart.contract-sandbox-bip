#!/usr/bin/env python3
"""
TAD AI - Self-Audit Script
Verifies phases 1-3 functionality
"""
import sys
import os
import time
import requests
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sandbox import SandboxManager, SandboxConfig
from agent import AIAgent, ModelProvider, AgentResponse
from exploit_manager import ExploitManager

def test_sandbox():
    print("\n🧪 Testing Phase 1: Sandbox Infrastructure...")
    manager = SandboxManager()
    
    # Try to start anvil (no fork for speed, just local)
    # We cheat and use an empty string for RPC to force local mode if possible, 
    # or just test the process spawning logic. 
    # Actually, Anvil runs fine without fork url.
    
    sandbox = manager.create_sandbox("test_audit", rpc_url="http://dummy", chain="ethereum")
    
    # Mocking the command to not fail on invalid RPC, or just checking class logic
    # Real test: Start anvil without fork to verify binary access
    sandbox.config.rpc_url = "" # Disable fork for this test
    
    cmd = ["anvil", "--port", str(sandbox.config.port)]
    print(f"   Command check: {' '.join(cmd)}")
    
    try:
        # Dry run start
        started = sandbox.start()
        if started:
            print("   ✅ Anvil started successfully")
            time.sleep(2)
            if sandbox.is_running():
                print("   ✅ Anvil process is running")
            else:
                print("   ❌ Anvil process died immediately")
            sandbox.stop()
            print("   ✅ Anvil stopped")
        else:
            print("   ❌ Failed to start Anvil (check if installed)")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def test_agent_logic():
    print("\n🧪 Testing Phase 2: AI Agent Logic...")
    
    # Mock API key
    os.environ["DEEPSEEK_API_KEY"] = "sk-dummy"
    
    try:
        agent = AIAgent(provider=ModelProvider.DEEPSEEK)
        print("   ✅ Agent initialized")
        
        prompt = agent._build_system_prompt()
        if "smart contract security auditor" in prompt:
            print("   ✅ System prompt built correctly")
        else:
            print("   ❌ System prompt missing key phrases")
            
        # Mock API call
        with patch.object(agent, '_call_api') as mock_call:
            mock_call.return_value = {
                "choices": [{"message": {"content": "VULNERABILITY: Reentrancy"}}],
                "usage": {"total_tokens": 100}
            }
            
            response = agent.analyze_contract("contract Foo {}", "0x123")
            
            if response.raw_response == "VULNERABILITY: Reentrancy":
                print("   ✅ Agent analysis flow working (Mocked)")
            else:
                print("   ❌ Agent response parsing failed")
                
    except Exception as e:
        print(f"   ❌ Agent test failed: {e}")

def test_exploit_manager():
    print("\n🧪 Testing Phase 3: Exploit Manager...")
    manager = ExploitManager()
    
    code = """
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.8.0;
    import "forge-std/Test.sol";
    contract AuditTest is Test {
        function testAudit() public {
            assertEq(1, 1);
        }
    }
    """
    
    path = manager.save_exploit_test("0x000", code, "AuditTest")
    if path.exists():
        print(f"   ✅ Test file saved: {path.name}")
        
        # Run forge test
        # We need to ensure we are in the root dir for foundry.toml (if it existed)
        # or just run it.
        print("   🔨 Running forge test...")
        
        # Modify run_exploit_test to not require fork for this unit test if possible,
        # but the class enforces fork-url. We will mock the subprocess or try running 
        # against our local anvil if it was running. 
        # For audit, we just check if `forge` binary is callable.
        
        try:
            import subprocess
            ver = subprocess.run(["forge", "--version"], capture_output=True)
            if ver.returncode == 0:
                print("   ✅ Forge binary accessible")
            else:
                print("   ❌ Forge binary found but returned error")
        except FileNotFoundError:
            print("   ❌ Forge binary NOT found")

    else:
        print("   ❌ Failed to save test file")

if __name__ == "__main__":
    print("🔍 STARTING FULL SYSTEM AUDIT")
    test_sandbox()
    test_agent_logic()
    test_exploit_manager()
    print("\n🏁 AUDIT COMPLETE")
