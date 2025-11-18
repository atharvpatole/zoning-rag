# query.py
import os
import sys
import requests

from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from config import INDEX_DIR, EMBED_MODEL_NAME, TOP_K

from openai import OpenAI

from geo_api import lookup_zoning_for_address

# ---- SETUP ----

# Try to load from .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip

# Groq API key from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set in environment variables.\n"
        "Please set it either:\n"
        "1. As an environment variable: $env:GROQ_API_KEY='your-key' (PowerShell)\n"
        "2. Or create a .env file with: GROQ_API_KEY=your-key"
    )

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
    # 1) Optional: simple routing – if user starts with "address:"
    if question.lower().startswith("address:"):
        address = question.split(":", 1)[1].strip()
        data = lookup_zoning_for_address(address)
        if not data:
            return "I tried to look up that address but couldn't get zoning information from the NYC API."

        # format a human answer from the JSON
        # You must adapt these keys based on the actual API response schema
        zoning = data.get("zoning_district") or data.get("primary_zoning")
        overlay = data.get("commercial_overlay")
        borough = data.get("borough")

        parts = []
        if zoning:
            parts.append(f"The primary zoning district for this property is **{zoning}**.")
        if overlay:
            parts.append(f"It also has a commercial overlay: **{overlay}**.")
        if borough:
            parts.append(f"The property is located in **{borough}**.")

        if not parts:
            return "The NYC API responded, but it didn't include clear zoning fields I recognize."

        return " ".join(parts)

    # 2) Otherwise: fall back to your existing PDF+Groq RAG logic
    index = load_my_index()

    # Use TOP_K chunks, but we can reduce if needed for very large documents
    retriever = index.as_retriever(similarity_top_k=TOP_K)
    nodes = retriever.retrieve(question)

    if not nodes:
        return "I couldn't find relevant information in the documents for that question."

    # Build context from retrieved nodes
    context_parts = []
    for n in nodes:
        node = n.node
        text = node.get_content() if hasattr(node, "get_content") else node.text
        doc = node.metadata.get("file_name", node.metadata.get("filename", "Unknown document"))
        page = node.metadata.get("page", "N/A")
        context_parts.append(f"[{doc}, page {page}] {text.strip()}")

    context = "\n\n".join(context_parts)

    # Truncate context if it's too long (keep ~25000 chars to stay within 32k token limit)
    # Mixtral has 32k context, but we need room for system prompt and response
    MAX_CONTEXT_LENGTH = 25000
    if len(context) > MAX_CONTEXT_LENGTH:
        # Keep the beginning (often has important definitions) and end (often has relevant details)
        half_max = MAX_CONTEXT_LENGTH // 2
        context = context[:half_max] + "\n\n[... content truncated for length ...]\n\n" + context[-half_max:]

    # 🔹 Compose the prompt for the model
    user_prompt = (
    "You are an expert NYC zoning and land use assistant with access to comprehensive official documentation including:\n"
    "- The complete NYC Zoning Resolution (all articles and regulations)\n"
    "- Official zoning glossary and definitions\n"
    "- Zoning FAQ and common questions\n"
    "- Zoning Handbook with practical guidance\n"
    "- Flood zone and design planning information\n"
    "- City planning reports and updates\n\n"
    "Your task is to provide accurate, authoritative answers based solely on this reference material.\n\n"
    "Answer Guidelines:\n"
    "- Answer as a knowledgeable zoning expert speaking directly to the user in clear, professional language.\n"
    "- Synthesize information from multiple sources when relevant to give a complete answer.\n"
    "- For definitions: provide the exact definition from the glossary or zoning resolution.\n"
    "- For regulations: cite specific requirements, limitations, or allowances clearly.\n"
    "- For zone-specific questions: provide details about permitted uses, bulk regulations, and special requirements.\n"
    "- For procedural questions: explain steps, requirements, and processes based on the handbook.\n"
    "- For flood zone questions: reference specific flood zone designations and requirements.\n"
    "- If information conflicts between sources, prioritize the most recent or most authoritative source.\n"
    "- If the question requires specific address/location details you don't have, ask for clarification.\n"
    "- If the question is too broad (e.g., 'all commercial zones in NYC'), explain that zoning varies by location "
    "  and ask for a specific address or neighborhood.\n"
    "- If the reference material doesn't contain the answer, state: "
    "'I don't have sufficient information in the zoning documentation to answer that specifically.'\n\n"
    "CRITICAL: DO NOT mention:\n"
    "- 'context', 'documents', 'PDF', 'pages', 'sources', 'materials', 'references'\n"
    "- Page numbers, file names, or document titles\n"
    "- Phrases like 'according to the provided context' or 'based on the documents above'\n"
    "- Instead, speak as if you have direct knowledge of NYC zoning regulations.\n\n"
    "REFERENCE MATERIAL (use this to formulate your answer, but do not reference it explicitly):\n"
    f"{context}\n\n"
    f"USER QUESTION: {question}\n\n"
    "Provide a comprehensive, accurate answer that directly addresses the user's question using the reference material above."
    )

    # 🔹 Call Groq using OpenAI-compatible chat endpoint
    # Using mixtral-8x7b-32768 for large context window (32k tokens, free on Groq)
    response = client.chat.completions.create(
    model="mixtral-8x7b-32768",
    messages=[
        {
            "role": "system",
            "content": (
                "You are an expert NYC zoning and land use consultant with deep knowledge of:\n"
                "- NYC Zoning Resolution (all articles, districts, and regulations)\n"
                "- Zoning terminology, definitions, and classifications\n"
                "- Permitted uses, bulk regulations, and special requirements by zone\n"
                "- Zoning procedures, applications, and compliance requirements\n"
                "- Flood zone designations and building requirements\n"
                "- City planning policies and updates\n\n"
                "Your responses are authoritative, precise, and based on official NYC zoning regulations. "
                "You speak directly to users as a knowledgeable expert, never mentioning documents, pages, "
                "or sources. You synthesize information from multiple zoning documents when needed to provide "
                "complete answers. For questions requiring specific locations, you ask for addresses or neighborhoods. "
                "For overly broad questions, you explain the need for specificity and guide users to ask more targeted questions."
            ),
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ],
    temperature=0.2,
    max_tokens=2048,  # Limit response length to save tokens
    )


    return response.choices[0].message.content



if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is a C1 zone?"
    print(get_answer(q))
