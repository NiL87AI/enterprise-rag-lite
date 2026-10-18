"""Conftest: disabilita reranker e dipendenze di rete nei test."""
import os
os.environ["RERANKER_ENABLED"] = "false"
