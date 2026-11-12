#!/usr/bin/env python3
"""
NetVision AI — Top-Level Execution Forwarder
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NESTED = ROOT / "NetVision-AI-SIH26153"

if (NESTED / "run_all.py").exists():
    os.chdir(str(NESTED))
    sys.path.insert(0, str(NESTED))
    import run_all
    run_all.main()
else:
    print(f"Error: {NESTED / 'run_all.py'} not found.")
    sys.exit(1)
