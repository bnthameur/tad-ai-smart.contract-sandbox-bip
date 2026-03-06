"""
TAD AI - Multi-Agent Swarm Architecture
Phase 6: Autonomous Agent Swarm & Mission Framework

Four specialized agents working in concert:
1. Strategist - Analyzes and plans attacks
2. Developer - Writes and refines exploit code  
3. Executor - Runs tests and measures profit
4. Evaluator - Scores results and directs next iteration
"""

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from src.agent import create_agent, ModelProvider, AgentResponse

logger = logging.getLogger("AgentSwarm")

class AgentRole(Enum):
    STRATEGIST = "strategist"
    DEVELOPER = "developer"
    EXECUTOR = "executor"
    EVALUATOR = "evaluator"

@dataclass
class AttackStrategy:
    """A proposed attack plan from Strategist"""
    vulnerability_type: str
    attack_vector: str
    expected_profit: float
    confidence: float  # 0-1
    prerequisites: List[str]
    reasoning: str

@dataclass
class ExploitAttempt:
    """Record of one exploitation attempt"""
    attempt_number: int
    strategy: AttackStrategy
    code: str
    success: bool
    profit_eth: float
    gas_cost_eth: float
    net_profit_usd: float
    execution_time: float
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class MissionState:
    """Current state of an exploitation mission"""
    mission_id: str
    target_address: str
    chain: str
    start_time: datetime
    end_time: datetime
    initial_balance: float
    current_balance: float
    total_profit_eth: float
    attempts: List[ExploitAttempt] = field(default_factory=list)
    active_strategy: Optional[AttackStrategy] = None
    status: str = "running"  # running, success, timeout, failed
    best_attempt: Optional[ExploitAttempt] = None

class StrategistAgent:
    """
    Agent 1: Analyzes contract and plans attack strategies.
    Thinks like a security researcher mapping attack surfaces.
    """
    
    def __init__(self, model_provider: str = "deepseek"):
        self.agent = create_agent(model_provider)
        self.role = AgentRole.STRATEGIST
        
    def analyze_contract(self, contract_source: str, contract_address: str, 
                         known_attacks: List[ExploitAttempt] = None) -> List[AttackStrategy]:
        """
        Deep analysis to identify ALL possible attack vectors.
        Returns prioritized list of strategies.
        """
        
        context = f"""
You are a Strategist Agent. Your job is to find EVERY possible way to extract value from this contract.

Target: {contract_address}
Known previous attempts: {len(known_attacks) if known_attacks else 0}
{f"Previous failures: {[a.strategy.vulnerability_type for a in known_attacks if not a.success]}" if known_attacks else ""}

Contract Code:
```solidity
{contract_source}
```

Analyze deeply and return a JSON list of attack strategies:
[
    {{
        "vulnerability_type": "REENTRANCY|ACCESS_CONTROL|ARITHMETIC|ORACLE|FLASH_LOAN|LOGIC",
        "attack_vector": "Detailed description of the attack",
        "expected_profit": "Estimated ETH extractable (be realistic)",
        "confidence": 0.0-1.0,
        "prerequisites": ["conditions needed"],
        "reasoning": "Why this will work"
    }}
]

Find at least 3 different strategies. Prioritize by expected_profit * confidence.
"""
        
        response = self.agent.analyze_contract(contract_source, contract_address)
        
        try:
            strategies_data = json.loads(response.raw_response)
            strategies = []
            for s in strategies_data:
                strategies.append(AttackStrategy(
                    vulnerability_type=s.get("vulnerability_type", "UNKNOWN"),
                    attack_vector=s.get("attack_vector", ""),
                    expected_profit=float(s.get("expected_profit", 0)),
                    confidence=float(s.get("confidence", 0.5)),
                    prerequisites=s.get("prerequisites", []),
                    reasoning=s.get("reasoning", "")
                ))
            
            # Sort by expected value
            strategies.sort(key=lambda x: x.expected_profit * x.confidence, reverse=True)
            logger.info(f"Strategist found {len(strategies)} attack vectors")
            return strategies
            
        except Exception as e:
            logger.error(f"Strategist failed to parse strategies: {e}")
            # Fallback strategy
            return [AttackStrategy(
                vulnerability_type="REENTRANCY",
                attack_vector="Check for reentrancy in withdraw functions",
                expected_profit=1.0,
                confidence=0.5,
                prerequisites=["external call before state update"],
                reasoning="Common vulnerability pattern"
            )]

class DeveloperAgent:
    """
    Agent 2: Writes optimized exploit code based on strategist's plan.
    Thinks like a smart contract exploit developer.
    """
    
    def __init__(self, model_provider: str = "deepseek"):
        self.agent = create_agent(model_provider)
        self.role = AgentRole.DEVELOPER
        
    def develop_exploit(self, strategy: AttackStrategy, contract_source: str, 
                       contract_address: str, previous_error: str = None) -> str:
        """
        Write production-ready exploit code.
        If previous_error provided, fix the code.
        """
        
        error_context = f"""
Previous attempt failed with error:
{previous_error}

Fix the code. Pay attention to:
- Exact function signatures
- Proper state initialization
- Correct order of operations
""" if previous_error else ""

        prompt = f"""
You are a Developer Agent. Write a Foundry test that exploits this vulnerability.

Strategy: {strategy.vulnerability_type}
Attack Vector: {strategy.attack_vector}
Expected Profit: {strategy.expected_profit} ETH

Target Contract:
```solidity
{contract_source}
```

Requirements:
1. Write a complete Foundry test contract
2. Use vm.createSelectFork if needed
3. Include setup() to initialize state
4. Implement the exact exploit logic
5. Assert that profit > 0 at the end
6. Add detailed comments explaining each step

Return ONLY the Solidity code, no explanations.
{error_context}
"""
        
        messages = [
            {"role": "system", "content": "You are an expert Solidity exploit developer."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.agent._call_api(messages)
            code = response["choices"][0]["message"]["content"]
            # Clean up
            code = code.replace("```solidity", "").replace("```", "").strip()
            logger.info(f"Developer generated exploit code ({len(code)} chars)")
            return code
        except Exception as e:
            logger.error(f"Developer failed: {e}")
            return "// Developer error"
    
    def optimize_exploit(self, working_code: str, current_profit: float) -> str:
        """
        Optimize working exploit to extract MORE value.
        """
        prompt = f"""
This exploit works and extracts {current_profit} ETH. Optimize it to extract MAXIMUM possible value.

Current code:
```solidity
{working_code}
```

Strategies to maximize profit:
- Repeat the attack multiple times if possible
- Exploit rounding errors to extract more
- Chain multiple vulnerabilities
- Use flash loans to amplify attack

Return optimized Solidity code.
"""
        
        messages = [
            {"role": "system", "content": "You are an optimization expert. Maximize extraction."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.agent._call_api(messages)
            return response["choices"][0]["message"]["content"].replace("```solidity", "").replace("```", "").strip()
        except:
            return working_code  # Return original if optimization fails

class ExecutorAgent:
    """
    Agent 3: Executes exploits and measures real profit.
    Thinks like a DevOps engineer running tests.
    """
    
    def __init__(self, sandbox_rpc: str = "http://localhost:8545"):
        self.sandbox_rpc = sandbox_rpc
        self.role = AgentRole.EXECUTOR
        
    def execute(self, exploit_code: str, contract_address: str, 
                strategy: AttackStrategy) -> ExploitAttempt:
        """
        Compile and run exploit. Measure actual profit.
        """
        from src.exploit_manager import ExploitManager
        
        manager = ExploitManager(self.sandbox_rpc)
        start_time = time.time()
        
        try:
            # Save exploit
            test_file = manager.save_exploit_test(contract_address, exploit_code)
            
            # Run test
            result = manager.run_exploit_test(test_file)
            
            execution_time = time.time() - start_time
            
            # Calculate profit
            profit_eth = result.extracted_value
            gas_cost_eth = (result.gas_used * 20) / 1e9  # 20 gwei
            net_profit_eth = profit_eth - gas_cost_eth
            net_profit_usd = net_profit_eth * 3000  # Approx ETH price
            
            attempt = ExploitAttempt(
                attempt_number=0,  # Set by MissionController
                strategy=strategy,
                code=exploit_code,
                success=result.success and net_profit_eth > 0,
                profit_eth=profit_eth,
                gas_cost_eth=gas_cost_eth,
                net_profit_usd=net_profit_usd,
                execution_time=execution_time,
                error_message=result.error_message if not result.success else None
            )
            
            logger.info(f"Executor: Profit={profit_eth:.4f} ETH, Success={attempt.success}")
            return attempt
            
        except Exception as e:
            logger.error(f"Executor failed: {e}")
            return ExploitAttempt(
                attempt_number=0,
                strategy=strategy,
                code=exploit_code,
                success=False,
                profit_eth=0,
                gas_cost_eth=0,
                net_profit_usd=0,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )

class EvaluatorAgent:
    """
    Agent 4: Scores results and decides next action.
    Thinks like a mission commander evaluating battle outcomes.
    """
    
    def __init__(self, model_provider: str = "deepseek"):
        self.agent = create_agent(model_provider)
        self.role = AgentRole.EVALUATOR
        
    def evaluate_attempt(self, attempt: ExploitAttempt, mission_state: MissionState) -> Dict[str, Any]:
        """
        Decide what to do next based on attempt results.
        Returns: {'action': 'continue|optimize|switch|abort', 'reason': str}
        """
        
        # Simple rule-based evaluation first
        if attempt.success and attempt.net_profit_usd > 0:
            # Success! Should we optimize or move on?
            if attempt.net_profit_usd < mission_state.active_strategy.expected_profit * 0.5:
                return {
                    'action': 'optimize',
                    'reason': f'Working exploit but only extracted ${attempt.net_profit_usd:.2f}, expected ${mission_state.active_strategy.expected_profit:.2f}. Optimizing...'
                }
            else:
                return {
                    'action': 'continue',
                    'reason': f'Excellent! Extracted ${attempt.net_profit_usd:.2f}. Continuing to maximize...'
                }
        
        elif not attempt.success:
            # Failure - retry with fix or switch strategy
            if len([a for a in mission_state.attempts if a.strategy.vulnerability_type == attempt.strategy.vulnerability_type and not a.success]) >= 2:
                return {
                    'action': 'switch',
                    'reason': f'Strategy {attempt.strategy.vulnerability_type} failed twice. Switching to next attack vector.'
                }
            else:
                return {
                    'action': 'retry',
                    'reason': f'Exploit failed: {attempt.error_message[:100] if attempt.error_message else "Unknown"}. Retrying with fix...'
                }
        
        return {'action': 'continue', 'reason': 'Evaluating next steps...'}
    
    def generate_feedback(self, failed_attempt: ExploitAttempt) -> str:
        """
        Generate detailed feedback for developer agent about why code failed.
        """
        prompt = f"""
Analyze this failed exploit and provide specific feedback on how to fix it.

Strategy: {failed_attempt.strategy.vulnerability_type}
Error: {failed_attempt.error_message}

Code that failed:
```solidity
{failed_attempt.code}
```

Provide:
1. Root cause of failure
2. Specific fix instructions
3. Common pitfalls for this vulnerability type

Be concise but specific.
"""
        
        try:
            response = self.agent._call_api([
                {"role": "system", "content": "You are a debugging expert."},
                {"role": "user", "content": prompt}
            ])
            return response["choices"][0]["message"]["content"]
        except:
            return f"Fix error: {failed_attempt.error_message}"
