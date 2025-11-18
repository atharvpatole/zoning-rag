# config.py

# where your PDF lives
PDF_DIR = "data_files"

# where LlamaIndex will store the index
INDEX_DIR = "index_store"

# local embedding model (free)
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Groq LLM model name (hosted; no GPU needed on your laptop)
# Using mixtral-8x7b-32768 for large context window (32k tokens)
GROQ_MODEL_NAME = "mixtral-8x7b-32768"

# how many chunks to retrieve per query
TOP_K = 10
