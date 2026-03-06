#!/usr/bin/env python3
"""
Contract source code fetching and analysis
"""

import os
import json
import requests
from typing import Optional, Dict, Any
from pathlib import Path


class ContractFetcher:
    """Fetches contract source code from blockchain explorers"""
    
    EXPLORER_APIS = {
        "ethereum": {
            "api": "https://api.etherscan.io/api",
            "env_key": "ETHERSCAN_API_KEY"
        },
        "bsc": {
            "api": "https://api.bscscan.com/api",
            "env_key": "BSCSCAN_API_KEY"
        },
        "polygon": {
            "api": "https://api.polygonscan.com/api",
            "env_key": "POLYGONSCAN_API_KEY"
        },
        "arbitrum": {
            "api": "https://api.arbiscan.io/api",
            "env_key": "ARBISCAN_API_KEY"
        }
    }
    
    def __init__(self, chain: str = "ethereum"):
        self.chain = chain.lower()
        self.api_config = self.EXPLORER_APIS.get(self.chain)
        
        if not self.api_config:
            raise ValueError(f"Unsupported chain: {chain}")
        
        self.api_key = os.getenv(self.api_config["env_key"])
        if not self.api_key:
            print(f"⚠️  Warning: {self.api_config['env_key']} not set. API may be rate-limited.")
    
    def fetch_source(self, address: str) -> Optional[Dict[str, Any]]:
        """Fetch contract source code from explorer"""
        
        params = {
            "module": "contract",
            "action": "getsourcecode",
            "address": address,
            "apikey": self.api_key or ""
        }
        
        try:
            print(f"🔍 Fetching source for {address} on {self.chain}...")
            response = requests.get(
                self.api_config["api"],
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "1":
                print(f"⚠️  API Error: {data.get('result', 'Unknown error')}")
                return None
            
            result = data["result"][0]
            
            return {
                "address": address,
                "chain": self.chain,
                "source_code": result.get("SourceCode"),
                "abi": result.get("ABI"),
                "contract_name": result.get("ContractName"),
                "compiler_version": result.get("CompilerVersion"),
                "optimization_used": result.get("OptimizationUsed"),
                "runs": result.get("Runs"),
                "constructor_arguments": result.get("ConstructorArguments"),
                "evm_version": result.get("EVMVersion"),
                "library": result.get("Library"),
                "license_type": result.get("LicenseType"),
                "proxy": result.get("Proxy"),
                "implementation": result.get("Implementation"),
                "swarm_source": result.get("SwarmSource")
            }
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def save_contract(self, contract_data: Dict[str, Any], output_dir: str = "contracts") -> str:
        """Save contract source to file"""
        
        address = contract_data["address"]
        chain = contract_data["chain"]
        name = contract_data.get("contract_name", "Unknown")
        
        # Create output directory
        out_path = Path(output_dir) / chain / address
        out_path.mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        with open(out_path / "metadata.json", "w") as f:
            json.dump(contract_data, f, indent=2)
        
        # Save source code
        source = contract_data.get("source_code", "")
        if source:
            with open(out_path / f"{name}.sol", "w") as f:
                f.write(source)
            print(f"💾 Saved to {out_path}/{name}.sol")
        
        return str(out_path)
    
    def fetch_abi(self, address: str) -> Optional[list]:
        """Fetch contract ABI"""
        params = {
            "module": "contract",
            "action": "getabi",
            "address": address,
            "apikey": self.api_key or ""
        }
        
        try:
            response = requests.get(
                self.api_config["api"],
                params=params,
                timeout=30
            )
            data = response.json()
            
            if data.get("status") == "1":
                return json.loads(data["result"])
            return None
        except:
            return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch contract source")
    parser.add_argument("address", help="Contract address")
    parser.add_argument("--chain", default="ethereum", help="Blockchain")
    parser.add_argument("--output", default="contracts", help="Output directory")
    
    args = parser.parse_args()
    
    fetcher = ContractFetcher(args.chain)
    contract = fetcher.fetch_source(args.address)
    
    if contract:
        path = fetcher.save_contract(contract, args.output)
        print(f"✅ Contract saved to {path}")
    else:
        print("❌ Failed to fetch contract")
