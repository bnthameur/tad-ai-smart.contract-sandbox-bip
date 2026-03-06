"""
TAD AI - Agent Module v2.0
Advanced Prompt Engineering & Autonomy
"""

import os
import json
import time
import logging
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Import our new prompt templates
from prompts.security_auditor import SYSTEM_PROMPT, REFINE_EXPLOIT_PROMPT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AIAgent")

class ModelProvider(Enum):
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    KIMI = "kimi"
    ANTHROPIC = "anthropic"

@dataclass
class AgentResponse:
    reasoning: str
    vulnerabilities: List[Dict[str, Any]]
    exploit_code: str
    raw_response: str
    tokens_used: int = 0
    cost: float = 0.0

class AIAgent:
    PRICING = {
        ModelProvider.DEEPSEEK: {"input": 0.27, "output": 1.10},
        ModelProvider.QWEN: {"input": 0.50, "output": 1.50},
        ModelProvider.KIMI: {"input": 0.50, "output": 2.00},
        ModelProvider.ANTHROPIC: {"input": 3.00, "output": 15.00},
    }
    
    def __init__(self, provider: ModelProvider, api_key: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key or self._get_api_key()
        self.model = self._default_model()
        self.total_cost = 0.0
        
    def _get_api_key(self) -> str:
        env_vars = {
            ModelProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
            ModelProvider.QWEN: "QWEN_API_KEY",
            ModelProvider.KIMI: "KIMI_API_KEY",
            ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
        }
        return os.getenv(env_vars[self.provider], "")
    
    def _default_model(self) -> str:
        defaults = {
            ModelProvider.DEEPSEEK: "deepseek-reasoner",
            ModelProvider.QWEN: "qwen3-235b-a22b",
            ModelProvider.KIMI: "kimi-k2",
            ModelProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
        }
        return defaults[self.provider]

    def _call_api(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Unified API caller with error handling"""
        if not self.api_key:
            logger.warning("No API Key - Running in Simulation Mode")
            return {
                "choices": [{"message": {"content": json.dumps({
                    "vulnerabilities": [{"name": "Simulated Reentrancy", "severity": "HIGH"}],
                    "exploit_poc": "// Simulated Exploit"
                })}}],
                "usage": {"total_tokens": 0}
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Adjust URL based on provider
        url = "https://api.deepseek.com/v1/chat/completions" # Default
        if self.provider == ModelProvider.KIMI:
            url = "https://api.moonshot.cn/v1/chat/completions"
        elif self.provider == ModelProvider.QWEN:
            url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

        for attempt in range(3):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "response_format": {"type": "json_object"}, # Enforce JSON
                        "temperature": 0.2
                    },
                    timeout=120
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.warning(f"API Attempt {attempt+1} failed: {e}")
                time.sleep(2)
        
        raise RuntimeError("API Call failed")

    def analyze_contract(self, contract_source: str, contract_address: str) -> AgentResponse:
        """
        Full autonomy loop:
        1. Inject System Prompt (Security Context)
        2. Send Code
        3. Parse JSON Response
        """
        logger.info(f"Analyzing contract at {contract_address}...")
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Target Address: {contract_address}\n\nCode:\n{contract_source}"}
        ]
        
        raw = self._call_api(messages)
        content = raw["choices"][0]["message"]["content"]
        tokens = raw["usage"]["total_tokens"]
        
        # Calculate cost
        pricing = self.PRICING[self.provider]
        cost = (tokens / 1_000_000) * pricing["output"] # Simplified
        self.total_cost += cost
        
        # Parse JSON output
        try:
            # Clean markdown code blocks if present
            clean_content = content.replace("```json", "").replace("```", "")
            data = json.loads(clean_content)
            
            return AgentResponse(
                reasoning="Automated Analysis",
                vulnerabilities=data.get("vulnerabilities", []),
                exploit_code=data.get("exploit_poc", ""),
                raw_response=content,
                tokens_used=tokens,
                cost=cost
            )
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response from agent")
            return AgentResponse("Parse Error", [], "", content, tokens, cost)

    def generate_exploit(self, context: str, source: str, address: str) -> str:
        # For refinement, we use the REFINE template
        messages = [
            {"role": "system", "content": "You are a Solidity Exploit Developer."},
            {"role": "user", "content": context} # Context contains error msg
        ]
        
        raw = self._call_api(messages)
        return raw["choices"][0]["message"]["content"]

def create_agent(provider: str = "deepseek") -> AIAgent:
    try:
        p = ModelProvider[provider.upper()]
    except:
        p = ModelProvider.DEEPSEEK
    return AIAgent(p)
