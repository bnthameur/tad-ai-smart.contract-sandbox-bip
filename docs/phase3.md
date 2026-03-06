# Phase 3: Real-Time Simulation Engine

## Overview
Phase 3 introduces the **Simulation Engine**, moving from static analysis to dynamic, real-time exploitation. It orchestrates the full lifecycle:
1.  **Fork Management:** Spawns ephemeral blockchain forks (Anvil).
2.  **Autonomous Agent:** AI analyzes code and writes Solidity exploits.
3.  **Execution Pipeline:** Compiles and runs exploits against the fork.
4.  **Profit Calculation:** Measures ETH extracted minus gas costs.

## Architecture

```
User Command
   ↓
SimulationEngine
   │
   ├── SandboxManager (Forks Chain)
   │       ↓
   │    Anvil Instance (Port 8545)
   │
   ├── AIAgent (DeepSeek/Qwen)
   │       ↓
   │    Analysis & Exploit Code
   │
   └── ExploitManager
           ↓
        Foundry (forge test)
           ↓
        Results (Profit/Gas)
```

## Usage

### Run a Simulation
```bash
export RPC_URL_MAINNET="https://eth-mainnet.g.alchemy.com/v2/..."
export DEEPSEEK_API_KEY="..."

python scripts/simulate_attack.py \
  0xC02aa... (WETH Address) \
  --chain ethereum \
  --block 19200000 \
  --model deepseek
```

### Metrics Output
The simulation returns:
*   **Vulnerability Found:** Did the AI identify an issue?
*   **Exploit Successful:** Did the `forge test` pass?
*   **Profit (ETH/USD):** Balance change of the attacker contract.
*   **Gas Cost:** Execution cost.

## Key Components

### `SimulationEngine` (`src/simulation.py`)
The main controller. It handles the dependency injection of the Agent, Fetcher, and Sandbox, ensuring proper cleanup (stopping Anvil) even if errors occur.

### `ExploitManager` (`src/exploit_manager.py`)
Now enhanced to parse `forge test` output for:
*   `gas used`
*   Custom logs indicating value extracted.

## Status
*   ✅ Basic Simulation Loop
*   ✅ Fork Integration
*   ✅ Exploit Execution
*   🚧 Advanced State Caching (Planned for Phase 3.5)
*   🚧 Flashbot Simulation (Planned for Phase 3.5)
