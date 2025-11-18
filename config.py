# config.py

# where your PDF lives
PDF_DIR = "data_files"

# where LlamaIndex will store the index
INDEX_DIR = "index_store"

# local embedding model (free)
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Groq LLM model name (hosted; no GPU needed on your laptop)
GROQ_MODEL_NAME = "llama3-8b-8192"

# how many chunks to retrieve per query
TOP_K = 10
