"""Compatibility entry point: all free readings use the plain-text pipeline."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.legacy_plain_entry import main

if __name__ == "__main__":
    raise SystemExit(main("daily"))
