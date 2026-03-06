"""
TAD AI - Agent Module v2.1
Multi-Provider API Support + Local Models
"""

import os
import json
import time
import logging
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from prompts.security_auditor import SYSTEM_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AIAgent")

class ModelProvider(Enum):
    DEEPSEEK = "deepseek"
    QWEN = "qwen" 
    KIMI = "kimi"
    ANTHROPIC = "anthropic"  # Claude
    OPENAI = "openai"        # GPT-4/GPT-4o
    GOOGLE = "google"        # Gemini
    LOCAL = "local"          # Ollama/vLLM

@dataclass
class AgentResponse:
    reasoning: str
    vulnerabilities: List[Dict[str, Any]]
    exploit_code: str
    raw_response: str
    tokens_used: int = 0
    cost: float = 0.0

class AIAgent:
    # Pricing per 1M tokens (input/output)
    PRICING = {
        ModelProvider.DEEPSEEK: {"input": 0.27, "output": 1.10},
        ModelProvider.QWEN: {"input": 0.50, "output": 1.50},
        ModelProvider.KIMI: {"input": 0.50, "output": 2.00},
        ModelProvider.ANTHROPIC: {"input": 3.00, "output": 15.00},
        ModelProvider.OPENAI: {"input": 5.00, "output": 15.00},
        ModelProvider.GOOGLE: {"input": 0.10, "output": 0.40},
        ModelProvider.LOCAL: {"input": 0.00, "output": 0.00},
    }
    
    def __init__(self, provider: ModelProvider, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key or self._get_api_key()
        self.base_url = base_url
        self.model = self._default_model()
        self.total_cost = 0.0
        
    def _get_api_key(self) -> str:
        env_map = {
            ModelProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
            ModelProvider.QWEN: "QWEN_API_KEY",
            ModelProvider.KIMI: "KIMI_API_KEY",
            ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            ModelProvider.OPENAI: "OPENAI_API_KEY",
            ModelProvider.GOOGLE: "GOOGLE_API_KEY",
            ModelProvider.LOCAL: "LOCAL_API_KEY",
        }
        return os.getenv(env_map.get(self.provider, ""), "")

    def _default_model(self) -> str:
        defaults = {
            ModelProvider.DEEPSEEK: "deepseek-reasoner",
            ModelProvider.QWEN: "qwen-max",
            ModelProvider.KIMI: "moonshot-v1-8k",
            ModelProvider.ANTHROPIC: "claude-3-5-sonnet-20240620",
            ModelProvider.OPENAI: "gpt-4o",
            ModelProvider.GOOGLE: "gemini-1.5-pro",
            ModelProvider.LOCAL: os.getenv("LOCAL_MODEL_NAME", "llama3"),
        }
        return defaults[self.provider]

    def _call_api(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Route to specific provider implementation"""
        if self.provider == ModelProvider.ANTHROPIC:
            return self._call_anthropic(messages)
        elif self.provider == ModelProvider.GOOGLE:
            return self._call_google(messages)
        else:
            return self._call_openai_compatible(messages)

    def _call_openai_compatible(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """DeepSeek, Qwen, Kimi, OpenAI, Local (Ollama)"""
        endpoints = {
            ModelProvider.DEEPSEEK: "https://api.deepseek.com/v1/chat/completions",
            ModelProvider.QWEN: "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            ModelProvider.KIMI: "https://api.moonshot.cn/v1/chat/completions",
            ModelProvider.OPENAI: "https://api.openai.com/v1/chat/completions",
            ModelProvider.LOCAL: os.getenv("LOCAL_LLM_URL", "http://localhost:11434/v1/chat/completions"),
        }
        
        url = endpoints[self.provider]
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2
        }
        
        # JSON mode for providers that support it
        if self.provider in [ModelProvider.OPENAI, ModelProvider.DEEPSEEK]:
            payload["response_format"] = {"type": "json_object"}

        for attempt in range(3):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=120)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.warning(f"Attempt {attempt+1} failed: {e}")
                time.sleep(2)
        
        raise RuntimeError("API failed after 3 retries")

    def _call_anthropic(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Claude API (unique format)"""
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_msgs = [m for m in messages if m["role"] != "system"]
        
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json={
            "model": self.model,
            "system": system,
            "messages": user_msgs,
            "max_tokens": 4096,
            "temperature": 0.2
        }, timeout=120)
        
        response.raise_for_status()
        data = response.json()
        
        return {
            "choices": [{"message": {"content": data["content"][0]["text"]}}],
            "usage": {"total_tokens": data["usage"]["input_tokens"] + data["usage"]["output_tokens"]}
        }

    def _call_google(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Google Gemini API"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        # Convert to Gemini format
        contents = []
        system_inst = None
        
        for m in messages:
            if m["role"] == "system":
                system_inst = {"parts": [{"text": m["content"]}]}
            else:
                role = "user" if m["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m["content"]}]})
        
        payload = {
            "contents": contents,
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
        }
        if system_inst:
            payload["system_instruction"] = system_inst

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
        
        return {
            "choices": [{"message": {"content": text}}],
            "usage": {"total_tokens": tokens}
        }

    def analyze_contract(self, contract_source: str, contract_address: str) -> AgentResponse:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Target: {contract_address}\n\nCode:\n{contract_source}"}
        ]
        
        try:
            raw = self._call_api(messages)
            content = raw["choices"][0]["message"]["content"]
            tokens = raw["usage"]["total_tokens"]
            
            # Calculate cost
            pricing = self.PRICING.get(self.provider, {"input": 0, "output": 0})
            cost = (tokens / 1_000_000) * pricing["output"]
            self.total_cost += cost
            
            # Parse JSON
            try:
                clean = content.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean)
                return AgentResponse("Success", data.get("vulnerabilities", []), 
                                   data.get("exploit_poc", ""), content, tokens, cost)
            except:
                return AgentResponse("Parse Error", [], "", content, tokens, cost)
                
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return AgentResponse(f"Error: {e}", [], "", "", 0, 0.0)

    def generate_exploit(self, context: str, source: str, address: str) -> str:
        messages = [
            {"role": "system", "content": "Return only Solidity code."},
            {"role": "user", "content": context}
        ]
        try:
            return self._call_api(messages)["choices"][0]["message"]["content"]
        except:
            return "// Error"

def create_agent(provider_name: str = "deepseek", **kwargs) -> AIAgent:
    try:
        p = ModelProvider[provider_name.upper()]
    except:
        logger.warning(f"Unknown provider {provider_name}, using DeepSeek")
        p = ModelProvider.DEEPSEEK
    return AIAgent(p, **kwargs)
