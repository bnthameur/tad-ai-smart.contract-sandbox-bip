# Testing Guide: Phases 1-3

Follow these steps to verify the stability of the TAD AI Sandbox.

## Prerequisites
Ensure you have Docker running and your environment variables set:
```bash
cp .env.example .env
# Edit .env and add your API keys (DeepSeek/Qwen) and RPC URL (Alchemy/Infura)
source .env
```

---

## 🧪 Phase 1: Environment & Sandbox
**Goal:** Verify Docker, Foundry, and Blockchain Forking work.

### 1. Build & Run Docker
```bash
docker build -t tad-ai-sandbox .
docker run -it --rm --env-file .env tad-ai-sandbox /bin/bash
```

### 2. Test Anvil Fork (Inside Container)
```bash
# Check tools
forge --version
anvil --version

# Test Forking (Ethereum Mainnet)
# Should start listening on 127.0.0.1:8545
anvil --fork-url $RPC_URL_MAINNET --fork-block-number 19200000
```

---

## 🤖 Phase 2: AI Agent & Analysis
**Goal:** Verify the AI can read code and find vulnerabilities.

### 1. Test Vulnerability Detection (Local Contract)
We included a vulnerable contract in `tests/contracts/VulnerableBank.sol`.

```bash
# Run analysis on local file
python scripts/analyze_phase2.py \
  --address 0x0000000000000000000000000000000000000000 \
  --chain ethereum \
  --model deepseek
```
*Note: Since it's local, the fetcher might fail on the address, but the agent initialization will be tested.*

### 2. Test Exploit Generation
Run the pre-written reentrancy exploit test to confirm Foundry is working correctly.

```bash
forge test --match-path tests/exploits/ReentrancyExploit.t.sol -vv
```
**Expected Output:** `[PASS]`

---

## ⚔️ Phase 3: Real-Time Simulation
**Goal:** Run the full "Game Loop" (Fork -> AI -> Attack -> Profit).

### 1. Run a Live Simulation
Pick a real contract address (e.g., a known vulnerable one or a simple DeFi contract).

```bash
python scripts/simulate_attack.py \
  0xYourTargetAddress \
  --chain ethereum \
  --block 19000000 \
  --model deepseek
```

**Check Reports:**
Results will be saved to `reports/sim_...md`.
