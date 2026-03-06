#!/usr/bin/env python3
"""
TAD AI - Dataset Curator
Phase 4: Manage historical vulnerability dataset
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from contract_fetcher import ContractFetcher

DATA_DIR = Path(__file__).parent.parent / "data/historical"
MANIFEST_FILE = DATA_DIR / "hacks.json"

def fetch_contracts():
    """Fetch source code for all contracts in manifest"""
    if not MANIFEST_FILE.exists():
        print("❌ Manifest not found")
        return

    with open(MANIFEST_FILE, "r") as f:
        hacks = json.load(f)
    
    print(f"📊 Found {len(hacks)} historical hacks")
    
    for hack in hacks:
        print(f"\n📥 Processing {hack['name']} ({hack['chain']})...")
        
        # Check if already fetched
        contract_dir = DATA_DIR / hack['chain'] / hack['address']
        if contract_dir.exists():
            print("   ✅ Already exists")
            continue
            
        fetcher = ContractFetcher(hack['chain'])
        contract = fetcher.fetch_source(hack['address'])
        
        if contract:
            path = fetcher.save_contract(contract, output_dir=str(DATA_DIR))
            print(f"   💾 Saved to {path}")
        else:
            print("   ❌ Failed to fetch")

if __name__ == "__main__":
    fetch_contracts()
