# # ingest.py
# from config import PDF_PATH, DB_DIR, CHUNK_SIZE, CHUNK_OVERLAP, EMBED_MODEL
# from pathlib import Path
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.document_loaders import PyMuPDFLoader
# from langchain_community.vectorstores import FAISS
# from langchain_community.embeddings import HuggingFaceEmbeddings
# # from langchain_openai import OpenAIEmbeddings


# def load_docs():
#     loader = PyMuPDFLoader(str(PDF_PATH))
#     return loader.load()  # pages as Documents (with metadata: page numbers)

# def split_docs(docs):
#     splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, separators=["\n\n", "\n", " ", ""],)
#     return splitter.split_documents(docs)

# def build_store(chunks):
#     embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
#     vs = FAISS.from_documents(chunks, embeddings)
#     vs.save_local(str(DB_DIR))
#     return vs

# if __name__ == "__main__":
#     if not PDF_PATH.exists():
#         raise FileNotFoundError(f"PDF not found at {PDF_PATH}")

#     docs = load_docs()
#     chunks = split_docs(docs)
#     build_store(chunks)
#     print(f"Indexed {len(chunks)} chunks into {DB_DIR}/")

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
