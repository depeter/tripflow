#!/usr/bin/env python3
"""
Simple script to run data sync from Scraparr to Tripflow.
Run from tripflow directory.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Now we can import
from app.sync.sync_cli import cli

if __name__ == "__main__":
    cli()
