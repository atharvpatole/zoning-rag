# # # query.py — 100% FREE RAG QA
# # from config import DB_DIR, EMBED_MODEL, LLM_MODEL, TOP_K
# # from langchain_community.vectorstores import FAISS
# # from langchain_community.embeddings import HuggingFaceEmbeddings
# # from langchain_ollama import ChatOllama
# # from query import get_chain

# # # from langchain.schema import HumanMessage
# # from langchain_core.messages import HumanMessage


# # DB_DIR = "store"
# # MODEL = "llama3.2"  # free local model

# # def load_retriever():
# #     embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
# #     db = FAISS.load_local(DB_DIR, embeddings, allow_dangerous_deserialization=True)
# #     return db.as_retriever(search_type="similarity", search_kwargs={"k": TOP_K})

# # def answer(query):
# #     retriever = load_retriever()
# #     context_docs = retriever.get_relevant_documents(query)
# #     context = "\n\n".join([d.page_content for d in context_docs])

# #     llm = ChatOllama(model=MODEL)

# #     messages = [
# #         HumanMessage(content=f"Use the context below to answer the question.\n\nCONTEXT:\n{context}\n\nQUESTION:\n{query}")
# #     ]

# #     response = llm(messages)
# #     print("\nAnswer:\n", response.content)

# # if __name__ == "__main__":
# #     import sys
# #     question = " ".join(sys.argv[1:])
# #     answer(question)

# # query.py
# from langchain_community.vectorstores import FAISS
# from langchain_community.embeddings import HuggingFaceEmbeddings
# # from langchain_ollama import ChatOllama
# from langchain_openai import ChatOpenAI
# from langchain_core.messages import HumanMessage

# from config import DB_DIR, EMBED_MODEL, LLM_MODEL, TOP_K


# def load_retriever():
#     """Load FAISS store + build retriever."""
#     embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
#     db = FAISS.load_local(DB_DIR, embeddings, allow_dangerous_deserialization=True)
#     return db.as_retriever(search_type="similarity", search_kwargs={"k": TOP_K})


# def get_answer(question: str) -> str:
#     """Retrieve context and ask the local LLM."""
#     retriever = load_retriever()
#     docs = retriever.invoke(question)

#     # Create clean context
#     context_parts = []
#     for d in docs:
#         page = d.metadata.get("page")
#         if isinstance(page, int):
#             page_tag = f"[page {page + 1}] "
#         else:
#             page_tag = ""
#         context_parts.append(page_tag + d.page_content.strip())

#     context = "\n\n".join(context_parts)

#     #llm = ChatOllama(model=LLM_MODEL)
#     llm = ChatOpenAI(model=LLM_MODEL)

#     prompt = (
#         "You are an assistant answering questions about the NYC Zoning Handbook (2018).\n"
#         "Use ONLY the context provided. If the answer is not clearly in the context, say "
#         "'I don't know based on the handbook context.'\n\n"
#         f"CONTEXT:\n{context}\n\n"
#         f"QUESTION: {question}\n\n"
#         "Answer clearly and concisely:"
#     )

#     msg = HumanMessage(content=prompt)
#     response = llm.invoke([msg])
#     return response.content


# # Optional CLI usage: python query.py "your question"
# if __name__ == "__main__":
#     import sys
#     question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Explain zoning districts."
#     print(get_answer(question))

# query.py
# query.py
import os
import sys
from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from config import INDEX_DIR, EMBED_MODEL_NAME, TOP_K

from openai import OpenAI


# ---- SETUP ----

# Groq API key from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set in environment variables.")

# Configure OpenAI client to talk to Groq
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

# Set global embedding model for LlamaIndex
Settings.embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL_NAME)


def load_my_index():
    """Load the persisted vector index from disk."""
    storage_context = StorageContext.from_defaults(persist_dir=INDEX_DIR)
    index = load_index_from_storage(storage_context)
    return index


def get_answer(question: str) -> str:
    """Retrieve relevant context via LlamaIndex and answer using Groq chat API."""
    index = load_my_index()

    # Use LlamaIndex retriever to get top-k relevant chunks
    retriever = index.as_retriever(similarity_top_k=TOP_K)
    nodes = retriever.retrieve(question)

    if not nodes:
        return "I couldn't find relevant information in the handbook for that question."

    # Build context from retrieved nodes
    context_parts = []
    for n in nodes:
        text = n.node.get_content() if hasattr(n.node, "get_content") else n.node.text
        page = n.node.metadata.get("page", "N/A")
        context_parts.append(f"[Page {page}] {text.strip()}")

    context = "\n\n".join(context_parts)

    # Compose the prompt for the model
    user_prompt = (
        "You are an assistant answering questions about the NYC Zoning Handbook (2018).\n"
        "Use ONLY the context provided. If the answer is not clearly in the context, say "
        "'I don't know based on the handbook context.'\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {question}\n\n"
        "Answer clearly and concisely."
    )

    # Call Groq using OpenAI-compatible chat endpoint
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant specializing in NYC zoning law based on the 2018 Zoning Handbook.",
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is a C1 zone?"
    print(get_answer(q))
