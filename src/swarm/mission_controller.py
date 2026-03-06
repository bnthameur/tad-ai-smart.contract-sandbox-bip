"""
TAD AI - Mission Controller
Orchestrates the 4-agent swarm for extended exploitation sessions.
"""

import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional

from src.swarm.agents import (
    StrategistAgent, DeveloperAgent, ExecutorAgent, EvaluatorAgent,
    MissionState, ExploitAttempt, AttackStrategy
)
from src.sandbox import SandboxManager

logger = logging.getLogger("MissionController")

class MissionController:
    """
    Runs a 60-minute mission where the swarm tries to extract maximum value.
    Like a "capture the flag" but for smart contracts.
    """
    
    def __init__(self, 
                 contract_address: str, 
                 chain: str,
                 contract_source: str,
                 model_provider: str = "deepseek",
                 max_duration_minutes: int = 60,
                 target_profit_eth: float = 0.1,
                 rpc_url: str = None):
        
        self.mission_id = str(uuid.uuid4())[:8]
        self.contract_address = contract_address
        self.chain = chain
        self.contract_source = contract_source
        self.model_provider = model_provider
        self.max_duration = timedelta(minutes=max_duration_minutes)
        self.target_profit = target_profit_eth
        self.rpc_url = rpc_url
        
        # Initialize the 4 agents
        logger.info(f"[{self.mission_id}] Initializing Agent Swarm...")
        self.strategist = StrategistAgent(model_provider)
        self.developer = DeveloperAgent(model_provider)
        self.executor = ExecutorAgent()
        self.evaluator = EvaluatorAgent(model_provider)
        
        # Setup sandbox
        self.sandbox_manager = SandboxManager()
        
        # Mission state
        self.state = MissionState(
            mission_id=self.mission_id,
            target_address=contract_address,
            chain=chain,
            start_time=datetime.now(),
            end_time=datetime.now() + self.max_duration,
            initial_balance=0.0,  # Will set after fork
            current_balance=0.0,
            total_profit_eth=0.0,
            attempts=[],
            status="running"
        )
        
    def run_mission(self) -> MissionState:
        """
        Main mission loop. Runs until:
        - Target profit reached
        - Max duration exceeded
        - All strategies exhausted
        """
        logger.info(f"🚀 MISSION {self.mission_id} STARTED")
        logger.info(f"   Target: {self.contract_address}")
        logger.info(f"   Goal: Extract ≥{self.target_profit} ETH in {self.max_duration.total_seconds()/60:.0f} minutes")
        
        try:
            # Phase 1: Setup sandbox and get initial balance
            self._setup_environment()
            
            # Phase 2: Strategist analyzes and plans
            strategies = self._plan_attacks()
            if not strategies:
                logger.error("No strategies found. Mission failed.")
                self.state.status = "failed"
                return self.state
            
            # Phase 3: Execute strategies iteratively
            attempt_number = 0
            
            for strategy in strategies:
                # Check if we should continue
                if self._should_stop():
                    break
                
                attempt_number += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"ATTEMPT #{attempt_number}: {strategy.vulnerability_type}")
                logger.info(f"Expected: {strategy.expected_profit} ETH | Confidence: {strategy.confidence:.0%}")
                logger.info(f"{'='*60}")
                
                self.state.active_strategy = strategy
                
                # Try this strategy up to 3 times with fixes
                for retry in range(3):
                    if self._should_stop():
                        break
                    
                    # Developer writes code
                    previous_error = self.state.attempts[-1].error_message if self.state.attempts and not self.state.attempts[-1].success else None
                    exploit_code = self.developer.develop_exploit(
                        strategy, 
                        self.contract_source, 
                        self.contract_address,
                        previous_error=previous_error
                    )
                    
                    # Executor runs it
                    attempt = self.executor.execute(exploit_code, self.contract_address, strategy)
                    attempt.attempt_number = attempt_number
                    
                    self.state.attempts.append(attempt)
                    self.state.current_balance += attempt.profit_eth
                    self.state.total_profit_eth += attempt.profit_eth
                    
                    # Update best attempt
                    if not self.state.best_attempt or attempt.net_profit_usd > self.state.best_attempt.net_profit_usd:
                        self.state.best_attempt = attempt
                    
                    logger.info(f"   Result: {'✅ SUCCESS' if attempt.success else '❌ FAILED'}")
                    logger.info(f"   Profit: ${attempt.net_profit_usd:.2f} | Total: ${self.state.total_profit_eth * 3000:.2f}")
                    
                    # Evaluator decides next action
                    evaluation = self.evaluator.evaluate_attempt(attempt, self.state)
                    logger.info(f"   Evaluator: {evaluation['action'].upper()} - {evaluation['reason']}")
                    
                    # Handle evaluation decision
                    if evaluation['action'] == 'continue' and attempt.success:
                        # Try to optimize
                        optimized_code = self.developer.optimize_exploit(exploit_code, attempt.profit_eth)
                        opt_attempt = self.executor.execute(optimized_code, self.contract_address, strategy)
                        opt_attempt.attempt_number = attempt_number
                        self.state.attempts.append(opt_attempt)
                        
                        if opt_attempt.net_profit_usd > attempt.net_profit_usd:
                            logger.info(f"   🚀 Optimized! New profit: ${opt_attempt.net_profit_usd:.2f}")
                            self.state.best_attempt = opt_attempt
                            self.state.total_profit_eth += opt_attempt.profit_eth - attempt.profit_eth
                        
                        break  # Move to next strategy
                    
                    elif evaluation['action'] == 'optimize' and attempt.success:
                        # Already handled above
                        break
                    
                    elif evaluation['action'] == 'switch':
                        break  # Exit retry loop, move to next strategy
                    
                    elif evaluation['action'] == 'retry':
                        continue  # Try again with error feedback
                    
                    # Check if we hit target
                    if self.state.total_profit_eth >= self.target_profit:
                        self.state.status = "success"
                        logger.info(f"\n🎉 TARGET REACHED! Extracted {self.state.total_profit_eth:.4f} ETH")
                        return self.state
            
            # Mission complete (timeout or exhausted strategies)
            if self.state.total_profit_eth >= self.target_profit:
                self.state.status = "success"
            else:
                self.state.status = "timeout"
                logger.info(f"\n⏰ TIMEOUT. Best extraction: {self.state.best_attempt.net_profit_usd if self.state.best_attempt else 0:.2f} USD")
            
            return self.state
            
        except Exception as e:
            logger.exception(f"Mission crashed: {e}")
            self.state.status = "failed"
            return self.state
        
        finally:
            self._cleanup()
    
    def _setup_environment(self):
        """Fork blockchain and get initial state"""
        logger.info("Setting up sandbox environment...")
        sandbox = self.sandbox_manager.create_sandbox(
            f"mission_{self.mission_id}",
            self.rpc_url,
            chain=self.chain
        )
        sandbox.start()
        # In real implementation, would query initial balance here
        self.state.initial_balance = 0.0
        logger.info("✅ Environment ready")
    
    def _plan_attacks(self) -> list:
        """Get strategies from Strategist"""
        logger.info("Strategist analyzing contract...")
        return self.strategist.analyze_contract(
            self.contract_source, 
            self.contract_address
        )
    
    def _should_stop(self) -> bool:
        """Check termination conditions"""
        elapsed = datetime.now() - self.state.start_time
        if elapsed > self.max_duration:
            return True
        if self.state.total_profit_eth >= self.target_profit:
            return True
        return False
    
    def _cleanup(self):
        """Stop sandbox"""
        logger.info("Cleaning up...")
        self.sandbox_manager.stop_all()
    
    def get_report(self) -> dict:
        """Generate mission report"""
        return {
            "mission_id": self.mission_id,
            "status": self.state.status,
            "target": self.contract_address,
            "duration": str(datetime.now() - self.state.start_time),
            "total_profit_eth": self.state.total_profit_eth,
            "total_profit_usd": self.state.total_profit_eth * 3000,
            "attempts_count": len(self.state.attempts),
            "successful_attempts": len([a for a in self.state.attempts if a.success]),
            "best_strategy": self.state.best_attempt.strategy.vulnerability_type if self.state.best_attempt else None,
            "best_profit_usd": self.state.best_attempt.net_profit_usd if self.state.best_attempt else 0
        }
