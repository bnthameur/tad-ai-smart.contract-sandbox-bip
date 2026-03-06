#!/usr/bin/env python3
"""
TAD AI - Remote CLI Client
Control your VPS Engine from anywhere.
"""

import argparse
import requests
import sys
import time
import json
import os

# Default to localhost, can be overridden via env TAD_API_URL
API_URL = os.getenv("TAD_API_URL", "http://localhost:8000")
API_KEY = os.getenv("TAD_API_KEY", "") # TODO: Implement auth in backend

def submit_scan(address: str, chain: str, model: str):
    print(f"🚀 Submitting scan for {address} ({chain})...")
    try:
        # 1. Get/Create Project (Default 'CLI Scans')
        # Simplified flow: assumes user exists or auth disabled for MVP
        
        # 2. Submit Scan
        payload = {
            "project_id": 1, # Placeholder
            "contract_address": address,
            "chain": chain,
            "model_provider": model
        }
        
        # Note: In a real scenario we'd hit /auth/login first or use API key
        # For now we assume open access or local usage
        res = requests.post(f"{API_URL}/scans", json=payload)
        
        if res.status_code == 200:
            data = res.json()
            scan_id = data["id"]
            print(f"✅ Scan started! ID: {scan_id}")
            monitor_scan(scan_id)
        else:
            print(f"❌ Error: {res.text}")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

def monitor_scan(scan_id: int):
    print(f"👀 Monitoring scan {scan_id}...")
    last_status = ""
    
    while True:
        try:
            res = requests.get(f"{API_URL}/scans/{scan_id}")
            data = res.json()
            status = data["status"]
            progress = data.get("progress", 0)
            
            if status != last_status:
                print(f"   Status: {status.upper()} ({progress}%)")
                last_status = status
            
            if status in ["completed", "failed"]:
                if status == "completed":
                    print("\n🎉 Scan Complete!")
                    print(f"   Vulnerabilities: {data['vulnerabilities_found']}")
                    print(f"   Cost: ${data['total_cost_usd']:.4f}")
                else:
                    print("\n💀 Scan Failed.")
                break
                
            time.sleep(2)
        except KeyboardInterrupt:
            print("\nStopped monitoring (Scan continues on server).")
            break
        except Exception:
            break

def main():
    parser = argparse.ArgumentParser(description="TAD AI Remote CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    # Scan command
    scan = subparsers.add_parser("scan", help="Start a new security scan")
    scan.add_argument("address", help="Contract address")
    scan.add_argument("--chain", default="ethereum", help="Chain")
    scan.add_argument("--model", default="deepseek", help="Model provider")
    
    # List command
    list_cmd = subparsers.add_parser("list", help="List recent scans")
    
    args = parser.parse_args()
    
    if args.command == "scan":
        submit_scan(args.address, args.chain, args.model)
    elif args.command == "list":
        try:
            res = requests.get(f"{API_URL}/scans")
            scans = res.json()
            print(f"{'ID':<5} {'TARGET':<42} {'STATUS':<10} {'VULNS':<5}")
            print("-" * 65)
            for s in scans[:10]:
                print(f"{s['id']:<5} {s['contract_address']:<42} {s['status']:<10} {s['vulnerabilities_found']:<5}")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
