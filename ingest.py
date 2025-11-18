# ingest.py
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from config import PDF_DIR, INDEX_DIR, EMBED_MODEL_NAME


def build_index():
    # load all files from the data/ directory
    docs = SimpleDirectoryReader(PDF_DIR).load_data()

    # set global embedding model for LlamaIndex
    embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL_NAME)
    Settings.embed_model = embed_model

    # build vector index
    index = VectorStoreIndex.from_documents(docs)

    # persist to disk so we can reuse it later
    storage_context = index.storage_context
    storage_context.persist(persist_dir=INDEX_DIR)

    print(f"Indexed {len(docs)} document(s) and saved to '{INDEX_DIR}'.")


if __name__ == "__main__":
    build_index()
