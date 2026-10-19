"""Conftest: disabilita reranker e dipendenze di rete nei test."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["RERANKER_ENABLED"] = "false"
