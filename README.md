# AI-Powered Smart Contract Security Sandbox

> Autonomous AI agents for detecting and exploiting smart contract vulnerabilities in a safe, forked blockchain sandbox.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Foundry](https://img.shields.io/badge/Built%20with-Foundry-FF7B72.svg)](https://book.getfoundry.sh/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://docker.com)

## 🎯 Overview

This project creates an **open-source framework** for AI-driven smart contract security auditing, inspired by Anthropic's SCONE-bench research. It combines:

- **Real-time blockchain forking** (Anvil/Foundry)
- **Containerized sandboxing** (Docker) for safe exploitation
- **AI agents** (DeepSeek, Qwen, Kimi) that analyze, exploit, and explain vulnerabilities
- **Educational focus** with multilingual support (EN/AR/FR)

### Key Innovation
Real-time blockchain forking + AI agent + Foundry testing = Automated security auditing accessible to developers with limited resources.

## 📊 Research Context

### Anthropic's SCONE-bench Breakthrough (Dec 2025)
- **51% exploit success rate** (207/405 contracts)
- **$550.1M** in simulated exploits discovered
- **$1.22** cost per contract
- **2 novel zero-days** found in live contracts

### Our Mission
Make this capability **open-source, cost-effective (<$0.50/contract), and accessible** to developers in Algeria/MENA and underserved regions.

## 🏗️ Architecture

```
User Input (Contract Address)
    ↓
┌─────────────────────────────────────┐
│  AI Agent                           │
│  (DeepSeek / Qwen / Kimi)          │
│  ↓                                  │
│  Tool Orchestrator (MCP-style)      │
│  ↓                                  │
│  • Fetch contract source            │
│  • Analyze vulnerabilities          │
│  • Generate exploit PoC             │
│  • Run Foundry tests                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Docker Sandbox                     │
│  ↓                                  │
│  Anvil (Forked Chain) :8545         │
│  ↓                                  │
│  Real-time state + Safe testing     │
└─────────────────────────────────────┘
    ↓
Report + Educational Content (EN/AR/FR)
```

## 📅 Roadmap (12 Months)

### Phase 1: Environment Setup (Months 1-2) ✅ COMPLETE
- [x] Docker image with Foundry toolchain
- [x] Anvil-based chain forking
- [x] CLI interface for sandbox management
- [x] Multi-chain support (Ethereum, BSC, Polygon)

### Phase 2: AI Agent Development (Months 3-5) ✅ COMPLETE
- [x] Model integration (DeepSeek, Qwen, Kimi)
- [x] Tool orchestration (MCP-style)
- [x] Prompt engineering for vulnerability detection
- [x] Iterative exploit generation

### Phase 3: Real-Time Simulation (Months 6-8) 🔄 PENDING
- [ ] Automated fork management
- [ ] Exploit execution pipeline
- [ ] Success metrics (balance delta, gas cost)
- [ ] State caching for repeated tests

### Phase 4: Dataset & Benchmarking (Months 9-10) 🔄 PENDING
- [ ] Curate 100+ historical exploited contracts
- [ ] Novel vulnerability hunting on live contracts
- [ ] Benchmark: detection rate, false positives, cost
- [ ] Publish dataset to GitHub

### Phase 5: Educational Framework (Months 11-12)
- [ ] Multilingual reports (EN/AR/FR)
- [ ] YouTube tutorial series
- [ ] CI/CD integration templates
- [ ] University course materials

## 🚀 Quick Start

### Prerequisites
- Docker (latest stable)
- Git
- Linux or WSL2 recommended
- API keys for model providers (optional)

### Installation

```bash
# Clone repository
git clone https://github.com/bnthameur/tad-ai-smart.contract-sandbox-bip.git
cd tad-ai-smart.contract-sandbox-bip

# Build Docker image
docker build -t tad-ai-sandbox .

# Run sandbox
docker run -it --rm \
  -e RPC_URL_MAINNET="https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY" \
  -e DEEPSEEK_API_KEY="your-key" \
  tad-ai-sandbox
```

### Verify Installation

```bash
# Inside container
forge --version  # Foundry
anvil --version  # Local EVM node
python3 --version
```

## 📖 Usage

### Analyze Contract by Address

```bash
python scripts/analyze_contract.py \
  --address 0xYourContractAddress \
  --chain ethereum \
  --block 19000000 \
  --model deepseek
```

### Analyze Local Source

```bash
python scripts/analyze_local.py \
  --path contracts/MyContract.sol \
  --model qwen
```

### CI/CD Integration

```yaml
- name: AI Security Audit
  uses: bnthameur/tad-ai-smart.contract-sandbox-bip@v1
  with:
    contract-address: ${{ secrets.CONTRACT_ADDRESS }}
    chain: ethereum
```

## 🧪 Testing

```bash
# Run Foundry tests
forge test

# Run Python unit tests
pytest tests/

# Run integration tests
./scripts/test_sandbox.sh
```

## 📚 Documentation

- [Architecture](docs/architecture.md) - System design details
- [API Reference](docs/api.md) - Tool specifications
- [Contributing](CONTRIBUTING.md) - How to contribute
- [Security](SECURITY.md) - Responsible disclosure

## 🌍 Educational Resources

This project is built **in public** as part of The Algerian Developer initiative:

- **YouTube**: Tutorial series on smart contract security
- **Blog**: Deep dives into vulnerability classes
- **Multilingual**: Reports in English, Arabic, and French

## ⚖️ Ethical Use

This framework is for **defensive security, education, and research only**:

✅ Use on contracts you own or have permission to test  
✅ Test on historical/publicly documented vulnerable contracts  
✅ Follow responsible disclosure for novel findings  
❌ Never use to steal funds or harm users  

## 🤝 Contributing

Contributions welcome from:
- Smart contract security researchers
- AI/tooling engineers
- Developers in MENA/underserved regions

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 🙏 Acknowledgements

- **Anthropic/MATS** for SCONE-bench pioneering research
- **Foundry/Anvil** maintainers for EVM tooling
- **Open-source security community** for datasets and research

## 📞 Contact

- **Twitter/X**: [@TheAlgerianDev](https://twitter.com/TheAlgerianDev)
- **YouTube**: [The Algerian Developer](https://youtube.com/@TheAlgerianDeveloper)
- **Email**: contact@thealgeriandeveloper.com

---

**Built with ❤️ in Algeria for the global Web3 security community.**
