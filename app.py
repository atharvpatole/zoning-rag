import os
import random
import streamlit as st

# --- LlamaIndex imports with backwards compatibility ---

try:
    # Old-style imports (if available)
    from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader
except ImportError:
    # New-style imports (llama_index >= 0.10+)
    from llama_index.core import VectorStoreIndex as GPTVectorStoreIndex
    from llama_index.core import SimpleDirectoryReader

try:
    from llama_index.llms import Groq
except ImportError:
    from llama_index.llms.groq import Groq

# ---------- Page configuration ----------
st.set_page_config(
    page_title="NYC Zoning AI Assistant",
    page_icon="🏙️",
    layout="wide",
)

DATA_DIR = "data_files"

# ---------- Cached loaders so we don't rebuild index every rerun ----------

@st.cache_resource(show_spinner="Indexing zoning PDFs…")
def load_index():
    documents = SimpleDirectoryReader(DATA_DIR).load_data()
    return GPTVectorStoreIndex.from_documents(documents)

@st.cache_resource(show_spinner="Connecting to LLM…")
def get_query_engine():
    index = load_index()
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        st.warning("GROQ_API_KEY is not set in the environment.")
    llm = Groq(model="mixtral-8x7b-32768", api_key=groq_api_key)
    return index.as_query_engine(llm=llm)

query_engine = get_query_engine()

# ---------- Session state for chat history and sidebar toggle ----------

if "messages" not in st.session_state:
    st.session_state.messages = []            # current conversation messages
if "conversations" not in st.session_state:
    st.session_state.conversations = []       # list of past conversations (for sidebar)
if "show_history" not in st.session_state:
    st.session_state.show_history = False     # sidebar (history) visibility

# ---------- Header with logo and buttons ----------

header_col1, header_col2, header_col3 = st.columns([0.7, 6, 0.7])

with header_col1:
    # Sidebar toggle button (☰)
    if st.button("☰", key="toggle_sidebar"):
        st.session_state.show_history = not st.session_state.show_history

with header_col2:
    # Centered app logo (note: use / not \ for cross-platform paths)
    st.image(f"{DATA_DIR}/marauders.jpeg", use_column_width=True)

with header_col3:
    # New chat button (＋)
    if st.button("＋", key="new_chat"):
        # Archive current conversation if not empty, then clear for new chat
        if st.session_state.messages:
            st.session_state.conversations.append(st.session_state.messages.copy())
        st.session_state.messages = []
        st.experimental_rerun()

# ---------- Expanders for Quick Tips, About, and Data sources ----------

with st.expander("Quick Tips", expanded=False):
    st.markdown(
        "- **Be specific:** Include details like location, zoning district, or relevant section numbers for more precise answers.\n"
        "- **Use zoning terms:** If you know terms such as *“use group”*, *“FAR”* (floor area ratio), or *“as-of-right”*, use them to focus the question.\n"
        "- **One question at a time:** Complex, multi-part questions can be harder for the assistant to answer effectively.\n"
        "- **Ask for definitions:** Not sure what a term means? You can ask, for example, *“What is a sky exposure plane?”*\n"
        "- **Refer to regulations:** If you know a Zoning Resolution section (e.g. *ZR 32-00*), mention it to get more targeted info."
    )

with st.expander("About", expanded=False):
    st.markdown(
        "**NYC Zoning AI Assistant** is a conversational tool to help you navigate New York City’s zoning regulations. "
        "It uses a large language model to answer your questions about zoning districts, land use rules, building size limits, special permits, and more. "
        "Under the hood, the app searches through NYC’s official zoning documents (the Zoning Resolution and related guides) to find relevant information, and uses an LLM to form its responses. "
        "Keep in mind that this assistant is for informational purposes only and **not an official source**. While it can help answer many common questions, *authoritative and complete answers must rely on the Zoning Resolution itself*. "
        "For detailed or situation-specific advice, you should consult the actual zoning text or contact the NYC Department of City Planning."
    )

with st.expander("Which Data Is Used?", expanded=False):
    st.markdown(
        "This assistant draws information from the following documents:\n"
        "- **All Articles ZR_23Sep2025_compressed.pdf** – *NYC Zoning Resolution (Articles I–XIV), updated September 2025*\n"
        "- **NYCP-Design-and-Planning-Flood-Zone__5b0f0f5da8144.pdf** – *Design and Planning for Flood Resiliency: Guidelines for NYC Parks (NYC Parks, 2020)*\n"
        "- **zoning-handbook-2018.pdf** – *NYC Zoning Handbook (2018 Edition)*"
    )

# ---------- Main chat interface layout ----------

if st.session_state.show_history:
    # If sidebar is toggled on, create two columns (sidebar for history, main for chat)
    sidebar_col, chat_col = st.columns([1.5, 5])
else:
    # If sidebar is off, use a single full-width column for chat
    chat_col = st.container()
    sidebar_col = None

# Sidebar: list past conversations when visible
if sidebar_col:
    with sidebar_col:
        st.markdown("**Chats**")
        if st.session_state.conversations:
            for i, conv in enumerate(st.session_state.conversations):
                if not conv:
                    continue  # skip empty conv
                # Use the first user message as the title (or generic label if not available)
                first_user_msg = next(
                    (msg["content"] for msg in conv if msg.get("role") == "user"),
                    "Conversation",
                )
                title = first_user_msg.strip()[:40]
                if len(first_user_msg) > 40:
                    title += "…"
                # Button to load that conversation
                if st.button(title, key=f"conv_{i}"):
                    # Save current convo if not empty
                    if st.session_state.messages:
                        st.session_state.conversations.append(
                            st.session_state.messages.copy()
                        )
                    # Load the selected convo into current messages
                    st.session_state.messages = conv.copy()
                    # Remove it from saved list (to avoid duplicates)
                    st.session_state.conversations.pop(i)
                    st.experimental_rerun()
        else:
            st.write("*(No previous chats)*")

# ---------- Chat column: display conversation and input ----------

with chat_col:
    # Display all past messages in the current conversation
    for msg in st.session_state.messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            with st.chat_message("user"):
                st.markdown(content)
        elif role == "assistant":
            with st.chat_message("assistant"):
                st.markdown(content)
        else:
            with st.chat_message(role):
                st.markdown(content)

    # Prepare rotating placeholder from example questions
    example_questions = [
        "What is the NYC Zoning Resolution?",
        "What does 'as-of-right development' mean in NYC zoning?",
        "Which uses are permitted in a C1-4 commercial overlay within an R7A district?",
        "My building was built before current zoning and doesn't conform to today's rules. Can I enlarge or change it?",
        "What design strategies does NYC recommend for parks in flood-prone areas?",
    ]
    placeholder_text = random.choice(example_questions)

    # Chat input box (appears at the bottom of the chat interface)
    user_input = st.chat_input(placeholder=placeholder_text)
    if user_input:
        # Store and show user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Generate answer using the LlamaIndex query engine and Groq LLM
        try:
            response = query_engine.query(user_input)
            answer_text = str(response)
        except Exception as e:
            answer_text = f"*(Error retrieving answer: {e})*"

        # Store and show assistant message
        st.session_state.messages.append({"role": "assistant", "content": answer_text})
        with st.chat_message("assistant"):
            st.markdown(answer_text)
