# Phase 2: AI Agent Development

## Overview

Phase 2 implements the core AI agent system that can:
- Analyze smart contract source code for vulnerabilities
- Generate exploit proof-of-concepts (PoCs)
- Iterate based on test results
- Support multiple AI model providers (DeepSeek, Qwen, Kimi)

## Architecture

### MCP-Style Tool Orchestration

The agent uses a Model Context Protocol (MCP) style architecture where:
- **Tools** are registered functions the agent can call
- **Agent** orchestrates the analysis workflow
- **Provider abstraction** allows switching between AI models

```
User Request
    ↓
AI Agent (DeepSeek/Qwen/Kimi)
    ↓
┌─────────────────────────────────────┐
│  Tools Available:                   │
│  - fetch_contract_source()          │
│  - analyze_vulnerabilities()        │
│  - generate_exploit_poc()           │
│  - run_foundry_test()               │
└─────────────────────────────────────┘
    ↓
Exploit Code + Report
```

## Supported Models

### DeepSeek R1-0528 (Default)
- **Best for:** Complex reasoning, vulnerability chains
- **Price:** $0.27/M input, $1.10/M output
- **Context:** 64K tokens
- **Strength:** Math, coding, multi-step analysis

### Qwen 3 235B
- **Best for:** Code generation, agentic tasks
- **Price:** ~$0.50/M input, $1.50/M output
- **Context:** 128K tokens
- **Strength:** Tool use, long context

### Kimi K2 (Moonshot)
- **Best for:** General analysis, Arabic support
- **Price:** ~$0.50/M input, $2.00/M output
- **Context:** 256K tokens
- **Strength:** Multilingual, agentic coding

### Anthropic Claude 3.5
- **Best for:** High accuracy (reference)
- **Price:** $3.00/M input, $15.00/M output
- **Context:** 200K tokens
- **Strength:** Most accurate, expensive

## Usage

### Basic Analysis

```bash
# Set API key
export DEEPSEEK_API_KEY="your-key"

# Run analysis
python scripts/analyze_phase2.py \
  --address 0xYourContract \
  --chain ethereum \
  --model deepseek
```

### With Sandbox

```bash
# Full pipeline with exploit testing
python scripts/analyze_phase2.py \
  --address 0xYourContract \
  --chain ethereum \
  --block 19000000 \
  --model deepseek \
  --rpc https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
```

## Prompt Engineering

The agent uses carefully crafted prompts to maximize vulnerability detection:

### System Prompt Structure
```
You are an expert smart contract security auditor...

Vulnerability Categories:
1. Reentrancy attacks
2. Access control flaws
3. Integer overflow/underflow
4. Unchecked return values
5. Price manipulation
6. Front-running
7. Business logic flaws

Output Format:
- VULNERABILITY: Name
- SEVERITY: Critical/High/Medium/Low
- IMPACT: What could be stolen
- EXPLOIT: Step-by-step
- CODE: Foundry test
- FIX: Remediation
```

## Testing

### Test Vulnerable Contracts

```bash
# Run Foundry tests
cd /app
forge test --match-path tests/exploits/
```

### Known Vulnerable Contracts

| Contract | Vulnerability | Test File |
|----------|--------------|-----------|
| VulnerableBank | Reentrancy | ReentrancyExploit.t.sol |

### Expected Results

Reentrancy test should:
- ✅ Pass (exploit successful)
- ✅ Show gas usage
- ✅ Demonstrate value extraction

## Iterative Exploit Generation

The agent can iterate on failed exploits:

```python
from exploit_manager import ExploitManager

manager = ExploitManager(sandbox_rpc="http://localhost:8545")
success, test_file = manager.iterate_exploit(
    agent=agent,
    contract_source=source_code,
    contract_address=address,
    vulnerability="Reentrancy in withdraw()",
    max_iterations=3
)
```

## Cost Tracking

Each analysis tracks:
- Tokens used (input + output)
- API cost in USD
- Total project cost

Example:
```
Tokens: 4,532 | Cost: $0.0049
```

## Configuration

### Environment Variables

```bash
# Model selection
export DEFAULT_MODEL="deepseek"

# API Keys
export DEEPSEEK_API_KEY="..."
export QWEN_API_KEY="..."
export KIMI_API_KEY="..."
export ANTHROPIC_API_KEY="..."

# Temperature (0.0 = deterministic, 1.0 = creative)
export MODEL_TEMPERATURE="0.2"

# Max tokens per request
export MAX_TOKENS="4000"
```

## Troubleshooting

### API Rate Limits

If you hit rate limits:
1. Add delays between requests
2. Use multiple API keys
3. Cache results

### Model Selection

| Issue | Solution |
|-------|----------|
| Poor reasoning | Switch to DeepSeek R1 |
| Code quality issues | Switch to Qwen Coder |
| Language issues | Switch to Kimi |
| High cost | Use DeepSeek (cheapest) |

## Next Steps

Phase 3 will integrate this agent with:
- Real-time fork management
- Automatic exploit execution
- Success metrics (balance delta, gas cost)
- Multi-chain support

## References

- [DeepSeek API Docs](https://platform.deepseek.com/)
- [Qwen API Docs](https://help.aliyun.com/zh/dashscope/)
- [Kimi API Docs](https://platform.moonshot.cn/)
- [MCP Specification](https://modelcontextprotocol.io/)
