"""Central configuration, read from environment variables."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Folder where documents live. Files placed here are indexed at startup.
DOCS_DIR = Path(os.getenv("DOCS_DIR", BASE_DIR / "sample_docs"))

# Chunking: size and overlap are measured in words.
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "120"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "30"))

# Retrieval: how many chunks are sent to the model as context.
TOP_K = int(os.getenv("TOP_K", "4"))
# Chunks scoring below this cosine similarity are treated as irrelevant.
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.05"))

# Claude settings. Without ANTHROPIC_API_KEY the app still runs in
# "retrieval only" mode and returns the best matching passages.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "700"))

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}
