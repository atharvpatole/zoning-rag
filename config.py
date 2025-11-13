# # config.py
# from pathlib import Path

# PDF_PATH = Path("zoning-handbook-2018.pdf")  # or Path("data/zoning-handbook-2018.pdf")
# DB_DIR = Path("store")
# EMBED_MODEL = "all-MiniLM-L6-v2"   # fast & cheap; swap if you prefer
# LLM_MODEL = "gpt-4o-mini"                # any modern chat model works
# # LLM_MODEL = "phi3:mini"
# CHUNK_SIZE = 1200
# CHUNK_OVERLAP = 150
# TOP_K = 4


# config.py

# where your PDF lives
PDF_DIR = "C:/Users/athar/OneDrive/Desktop/raw"

# where LlamaIndex will store the index
INDEX_DIR = "index_store"

# local embedding model (free)
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Groq LLM model name (hosted; no GPU needed on your laptop)
GROQ_MODEL_NAME = "llama3-8b-8192"

# how many chunks to retrieve per query
TOP_K = 4
