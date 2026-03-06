#!/usr/bin/env python3
"""
TAD AI - Worker Status CLI
Check what the workers are doing
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.orchestrator import get_orchestrator

def main():
    parser = argparse.ArgumentParser(description="Check worker status")
    parser.add_argument("--worker", help="Specific worker name (alpha, beta, gamma)")
    parser.add_argument("--cancel", help="Cancel a worker by name")
    
    args = parser.parse_args()
    
    orch = get_orchestrator()
    
    if args.cancel:
        success = orch.cancel_worker(args.cancel)
        if success:
            print(f"✅ Cancelled {args.cancel}")
        else:
            print(f"❌ Failed to cancel {args.cancel}")
        return
    
    if args.worker:
        status = orch.get_status(args.worker)
        print(f"\n📋 {args.worker.upper()} Status:")
        print(f"   Status: {status['status']}")
        print(f"   Task: {status['task']}")
        print(f"   Progress: {status['progress']}%")
    else:
        print(orch.get_summary())

if __name__ == "__main__":
    main()
