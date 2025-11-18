# app.py
import streamlit as st
from datetime import datetime

from query import get_answer


# Helper functions
def normalize_timestamp(ts):
    """Return a datetime for any timestamp value (str/datetime/None)."""
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts)
        except ValueError:
            pass
    return datetime.min


def last_message_timestamp(messages):
    """Safely get the last message timestamp from a chat."""
    if not messages:
        return datetime.min
    ts = messages[-1].get("timestamp") if isinstance(messages[-1], dict) else None
    return normalize_timestamp(ts)


# Page configuration - responsive
st.set_page_config(
    page_title="NYC Zoning Assistant",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add responsive CSS
st.markdown("""
    <style>
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header {
            flex-direction: column;
            gap: 0.5rem;
        }
        .header-buttons {
            width: 100%;
            justify-content: space-between;
        }
    }
    
    /* Fix button styling */
    .stButton > button {
        white-space: nowrap;
    }
    
    /* Ensure proper spacing */
    .main-content {
        padding: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "chat_counter" not in st.session_state:
    st.session_state.chat_counter = 0

if "sidebar_visible" not in st.session_state:
    st.session_state.sidebar_visible = True

if "placeholder_index" not in st.session_state:
    st.session_state.placeholder_index = 0
if "rerun_count" not in st.session_state:
    st.session_state.rerun_count = 0

# Example questions for dynamic placeholder
example_questions = [
    "What is a C1 zone?",
    "What are the bulk regulations for R6?",
    "What uses are allowed in commercial districts?",
    "Explain the regulations for an R6 district.",
    "What are the zoning districts in Manhattan?",
]

# Increment rerun count and rotate placeholder every 5 reruns (when no input)
st.session_state.rerun_count += 1
if st.session_state.rerun_count % 5 == 0:
    st.session_state.placeholder_index = (st.session_state.placeholder_index + 1) % len(example_questions)

# Get current placeholder
current_placeholder = example_questions[st.session_state.placeholder_index % len(example_questions)]

# Header with toggle button and new chat
header_col1, header_col2, header_col3 = st.columns([1, 10, 1])

with header_col1:
    if st.button(">>", key="toggle_sidebar", help="Toggle sidebar"):
        st.session_state.sidebar_visible = not st.session_state.sidebar_visible
        st.rerun()

with header_col2:
    st.title("NYC Zoning Assistant")
    
    # About and Quick Tips below title
    with st.expander("About", expanded=False):
        st.markdown("""
        This assistant provides expert answers about:
        - Zoning districts and regulations
        - Permitted uses and bulk requirements
        - Zoning procedures and compliance
        - Flood zones and design requirements
        - City planning policies
        """)
    
    with st.expander("Quick Tips", expanded=False):
        st.markdown("""
        - Ask specific questions for best results
        - Use **address:** prefix for location lookups
        - Examples:
          - "What is a C1 zone?"
          - "address: 123 Main St, Manhattan"
          - "What are the bulk regulations for R6?"
        """)

with header_col3:
    if st.button("+", key="new_chat_btn", help="New Chat"):
        st.session_state.chat_counter += 1
        new_id = f"chat_{st.session_state.chat_counter}"
        st.session_state.chats[new_id] = []
        st.session_state.current_chat_id = new_id
        st.rerun()

# Ensure we always have a current chat
if st.session_state.current_chat_id is None:
    st.session_state.chat_counter += 1
    first_id = f"chat_{st.session_state.chat_counter}"
    st.session_state.chats[first_id] = []
    st.session_state.current_chat_id = first_id

# Layout: Sidebar and main area (responsive)
if st.session_state.sidebar_visible:
    sidebar_col, main_col = st.columns([2, 8])
else:
    main_col = st.container()
    sidebar_col = None

# Sidebar for conversation list
if sidebar_col is not None:
    with sidebar_col:
        st.header("Conversations")
        
        chats = st.session_state.chats
        # Filter out empty chats (only show chats with messages)
        chats_with_messages = {k: v for k, v in chats.items() if v}
        
        if chats_with_messages:
            sorted_chats = sorted(
                chats_with_messages.items(),
                key=lambda x: last_message_timestamp(x[1]),
                reverse=True,
            )
            
            for chat_id, messages in sorted_chats:
                first_user = next((m for m in messages if m.get("role") == "user"), None)
                if first_user:
                    title_text = first_user["content"]
                else:
                    title_text = "Untitled"
                
                if len(title_text) > 40:
                    title = title_text[:40] + "..."
                else:
                    title = title_text
                
                is_active = chat_id == st.session_state.current_chat_id
                
                if st.button(title, key=f"chat_{chat_id}", use_container_width=True):
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
        else:
            st.caption("No conversations yet. Click + to start a new chat.")

# Main chat area
with main_col:
    current_chat = st.session_state.chats.get(st.session_state.current_chat_id, [])
    
    # Display chat messages
    if current_chat:
        for msg in current_chat:
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            with st.chat_message(role):
                st.markdown(content)
    
    # Chat input with dynamic placeholder
    prompt = st.chat_input(current_placeholder)
    
    if prompt:
        # Reset rerun count when user inputs something
        st.session_state.rerun_count = 0
        # Store and show user message
        user_msg = {
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat(),
        }
        current_chat.append(user_msg)
        st.session_state.chats[st.session_state.current_chat_id] = current_chat
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    answer = get_answer(prompt)
                except Exception as e:
                    answer = (
                        "There was an unexpected error while processing your request. "
                        "Please try again or rephrase your question.\n\n"
                        f"Details: {e}"
                    )
                st.markdown(answer)
        
        assistant_msg = {
            "role": "assistant",
            "content": answer,
            "timestamp": datetime.now().isoformat(),
        }
        current_chat.append(assistant_msg)
        st.session_state.chats[st.session_state.current_chat_id] = current_chat
        st.rerun()
