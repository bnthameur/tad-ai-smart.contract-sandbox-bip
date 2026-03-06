# Phase 4: Dataset & Benchmarking

## Overview
Phase 4 establishes a rigorous evaluation framework inspired by Anthropic's SCONE-bench, but fully open-source.

## Dataset: Historical Exploits (`data/historical/`)

### Structure
```
data/historical/
├── hacks.json              # Manifest of exploits
├── ethereum/
│   └── 0x.../             # Contract address
│       ├── Contract.sol    # Source code
│       └── metadata.json   # ABI, compiler info
└── bsc/
    └── ...
```

### Manifest Format (`hacks.json`)
Each entry contains:
- `name`: Protocol name
- `address`: Contract address
- `chain`: Blockchain (ethereum, bsc, polygon)
- `vulnerability_type`: Reentrancy, Oracle, Logic, etc.
- `loss_amount`: USD lost
- `date`: Exploit date
- `description`: Technical summary

### Initial Dataset (3 contracts)
| Name | Chain | Type | Loss | Date |
|------|-------|------|------|------|
| Uranium Finance | BSC | Logic Error | $50M | 2021-04 |
| Value DeFi | ETH | Oracle | $6M | 2020-11 |
| Euler Finance | ETH | Logic | $197M | 2023-03 |

*Expandable to 100+ contracts from Rekt, DeFiHackLabs*

## Benchmarking Harness (`scripts/benchmark.py`)

### Metrics Tracked
1. **Detection Rate** (% of known vulns found)
2. **Exploit Generation Rate** (% with working PoC)
3. **Cost Efficiency** ($ per contract)
4. **Speed** (avg time per analysis)
5. **False Positive Rate** (manual verification needed)

### Usage
```bash
# Benchmark DeepSeek on 10 contracts
python scripts/benchmark.py --model deepseek --sample 10

# Benchmark Claude
python scripts/benchmark.py --model anthropic --sample 10

# Compare all models
for model in deepseek qwen kimi openai anthropic google; do
    python scripts/benchmark.py --model $model --sample 5
done
```

### Output
```
REPORT: DEEPSEEK
Total Contracts:    10
Vulns Detected:     8 (80.0%)
Exploits Generated: 6 (60.0%)
Total Cost:         $0.0456
Avg Cost/Contract:  $0.0046
Avg Time/Contract:  12.3s
```

## Comparison to SCONE-bench

| Feature | Anthropic SCONE | TAD AI (This) |
|---------|----------------|---------------|
| Open Source | ❌ Closed | ✅ Open |
| Cost | $1.22/contract | ~$0.50/contract |
| Models | Claude only | 7+ providers |
| Languages | English | EN/AR/FR |
| Exploit Exec | ✅ Yes | ✅ Yes |
| Dataset Size | 405 contracts | Growing to 100+ |

## Next: Phase 5
Educational framework and multilingual reporting.
