#!/usr/bin/env python3
"""Executable runner for jwt-inspector."""
import sys
from jwt_inspector.cli import main

if __name__ == "__main__":
    sys.exit(main())
