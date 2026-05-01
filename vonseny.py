#!/usr/bin/env python3
"""Proje kökünden 'python vonseny.py ...' ile çalıştırmak için kısa yol."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from vonseny.vonseny import main

if __name__ == "__main__":
    main()
