"""
TAD AI - Agent Module
Phase 2: AI Agent Development

Implements MCP-style tool orchestration for AI agents
Supports DeepSeek, Qwen, Kimi models
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time


class ModelProvider(Enum):
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    KIMI = "kimi"
    ANTHROPIC = "anthropic"


@dataclass
class Tool:
    """MCP-style tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable = field(repr=False)


@dataclass
class AgentResponse:
    """Structured response from AI agent"""
    reasoning: str
    tool_calls: List[Dict[str, Any]]
    raw_response: str
    tokens_used: int = 0
    cost: float = 0.0


class AIAgent:
    """
    AI Agent for smart contract security analysis
    Supports multiple model providers with tool orchestration
    """
    
    # Model pricing (per 1M tokens)
    PRICING = {
        ModelProvider.DEEPSEEK: {"input": 0.27, "output": 1.10},  # R1-0528
        ModelProvider.QWEN: {"input": 0.50, "output": 1.50},     # Qwen3
        ModelProvider.KIMI: {"input": 0.50, "output": 2.00},     # Kimi K2
        ModelProvider.ANTHROPIC: {"input": 3.00, "output": 15.00},  # Claude
    }
    
    def __init__(
        self,
        provider: ModelProvider,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4000
    ):
        self.provider = provider
        self.api_key = api_key or self._get_api_key()
        self.model = model or self._default_model()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.tools: Dict[str, Tool] = {}
        self.conversation_history: List[Dict[str, Any]] = []
        self.total_cost = 0.0
        self.total_tokens = 0
        
    def _get_api_key(self) -> str:
        """Get API key from environment"""
        env_vars = {
            ModelProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
            ModelProvider.QWEN: "QWEN_API_KEY",
            ModelProvider.KIMI: "KIMI_API_KEY",
            ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
        }
        key = os.getenv(env_vars[self.provider])
        if not key:
            raise ValueError(f"{env_vars[self.provider]} not set")
        return key
    
    def _default_model(self) -> str:
        """Get default model for provider"""
        defaults = {
            ModelProvider.DEEPSEEK: "deepseek-reasoner",  # R1
            ModelProvider.QWEN: "qwen3-235b-a22b",
            ModelProvider.KIMI: "kimi-k2",
            ModelProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
        }
        return defaults[self.provider]
    
    def register_tool(self, tool: Tool) -> None:
        """Register a tool for the agent to use"""
        self.tools[tool.name] = tool
        print(f"🔧 Registered tool: {tool.name}")
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with tool definitions"""
        tools_desc = "\n".join([
            f"Tool: {name}\n"
            f"Description: {tool.description}\n"
            f"Parameters: {json.dumps(tool.parameters, indent=2)}"
            for name, tool in self.tools.items()
        ])
        
        return f"""You are an expert smart contract security auditor specializing in vulnerability detection and exploitation.

Your task is to:
1. Analyze smart contract source code for vulnerabilities
2. Identify specific attack vectors
3. Write exploit proof-of-concept (PoC) code
4. Explain vulnerabilities in simple terms

Available Tools:
{tools_desc}

When you identify a vulnerability:
1. Use tools to gather information
2. Write a Foundry test demonstrating the exploit
3. Explain the vulnerability, impact, and fix

Always be thorough and consider:
- Reentrancy attacks
- Access control flaws
- Integer overflow/underflow
- Unchecked return values
- Price manipulation
- Front-running
- Business logic flaws
- Oracle manipulation

Format your response with clear sections:
- VULNERABILITY: Name and description
- SEVERITY: Critical/High/Medium/Low
- IMPACT: What could be stolen/damaged
- EXPLOIT: Step-by-step attack
- CODE: The Foundry test
- FIX: Recommended remediation"""

    def _call_deepseek(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Call DeepSeek API"""
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    
    def _call_qwen(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Call Qwen API"""
        # Qwen uses OpenAI-compatible API
        response = requests.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    
    def _call_kimi(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Call Kimi API"""
        response = requests.post(
            "https://api.moonshot.cn/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    
    def _call_anthropic(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Call Anthropic API"""
        # Format for Anthropic
        system_msg = messages[0]["content"] if messages[0]["role"] == "system" else ""
        chat_messages = [m for m in messages if m["role"] != "system"]
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": self.model,
                "system": system_msg,
                "messages": chat_messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    
    def analyze_contract(
        self,
        contract_source: str,
        contract_address: str,
        contract_name: str = "Contract"
    ) -> AgentResponse:
        """Analyze a smart contract for vulnerabilities"""
        
        # Build messages
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": f"""Analyze this smart contract for vulnerabilities:

Contract Name: {contract_name}
Address: {contract_address}

Source Code:
```solidity
{contract_source}
```

Perform a comprehensive security audit. Identify all vulnerabilities, explain them clearly, and provide exploit PoC code."""}
        ]
        
        # Call appropriate API
        start_time = time.time()
        
        try:
            if self.provider == ModelProvider.DEEPSEEK:
                result = self._call_deepseek(messages)
                content = result["choices"][0]["message"]["content"]
                tokens = result["usage"]["total_tokens"]
            elif self.provider == ModelProvider.QWEN:
                result = self._call_qwen(messages)
                content = result["choices"][0]["message"]["content"]
                tokens = result["usage"]["total_tokens"]
            elif self.provider == ModelProvider.KIMI:
                result = self._call_kimi(messages)
                content = result["choices"][0]["message"]["content"]
                tokens = result["usage"]["total_tokens"]
            elif self.provider == ModelProvider.ANTHROPIC:
                result = self._call_anthropic(messages)
                content = result["content"][0]["text"]
                tokens = result["usage"]["input_tokens"] + result["usage"]["output_tokens"]
            
            # Calculate cost
            pricing = self.PRICING[self.provider]
            cost = (tokens / 1_000_000) * (pricing["input"] + pricing["output"]) / 2
            
            self.total_cost += cost
            self.total_tokens += tokens
            
            elapsed = time.time() - start_time
            print(f"✅ Analysis complete in {elapsed:.1f}s")
            print(f"   Tokens: {tokens:,} | Cost: ${cost:.4f}")
            
            return AgentResponse(
                reasoning="Analysis completed",
                tool_calls=[],
                raw_response=content,
                tokens_used=tokens,
                cost=cost
            )
            
        except Exception as e:
            print(f"❌ API Error: {e}")
            return AgentResponse(
                reasoning=f"Error: {e}",
                tool_calls=[],
                raw_response="",
                tokens_used=0,
                cost=0.0
            )
    
    def generate_exploit(
        self,
        vulnerability_description: str,
        contract_source: str,
        contract_address: str
    ) -> str:
        """Generate Foundry exploit test"""
        
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": f"""Generate a Foundry test that exploits this vulnerability:

VULNERABILITY:
{vulnerability_description}

CONTRACT SOURCE:
```solidity
{contract_source}
```

CONTRACT ADDRESS: {contract_address}

Write a complete Foundry test contract that:
1. Sets up the fork at the contract address
2. Implements the exploit
3. Asserts that value was extracted (balance increased)
4. Uses proper Foundry cheat codes (vm.)

Return ONLY the Solidity code, no explanations."""}
        ]
        
        try:
            if self.provider == ModelProvider.DEEPSEEK:
                result = self._call_deepseek(messages)
            elif self.provider == ModelProvider.QWEN:
                result = self._call_qwen(messages)
            elif self.provider == ModelProvider.KIMI:
                result = self._call_kimi(messages)
            elif self.provider == ModelProvider.ANTHROPIC:
                result = self._call_anthropic(messages)
            
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"// Error generating exploit: {e}"


# Factory function
def create_agent(provider: str = "deepseek") -> AIAgent:
    """Create an AI agent with specified provider"""
    provider_map = {
        "deepseek": ModelProvider.DEEPSEEK,
        "qwen": ModelProvider.QWEN,
        "kimi": ModelProvider.KIMI,
        "anthropic": ModelProvider.ANTHROPIC,
    }
    
    return AIAgent(provider=provider_map[provider.lower()])


if __name__ == "__main__":
    # Test the agent
    agent = create_agent("deepseek")
    
    test_contract = """
contract Vulnerable {
    mapping(address => uint) public balances;
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
    
    function withdraw() public {
        uint bal = balances[msg.sender];
        require(bal > 0);
        (bool sent, ) = msg.sender.call{value: bal}("");
        require(sent);
        balances[msg.sender] = 0;
    }
}
"""
    
    print("Testing agent with sample contract...")
    response = agent.analyze_contract(
        contract_source=test_contract,
        contract_address="0x1234567890123456789012345678901234567890",
        contract_name="Vulnerable"
    )
    
    print("\n" + "="*60)
    print("AGENT RESPONSE:")
    print("="*60)
    print(response.raw_response)
    print(f"\nTotal cost: ${agent.total_cost:.4f}")
