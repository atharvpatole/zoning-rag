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


# Page configuration
st.set_page_config(
    page_title="NYC Zoning Assistant",
    page_icon=None,
    layout="wide"
)

# Initialize session state
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "chat_counter" not in st.session_state:
    st.session_state.chat_counter = 0

if "sidebar_visible" not in st.session_state:
    st.session_state.sidebar_visible = True

# Header with toggle button
col1, col2, col3 = st.columns([1, 8, 1])

with col1:
    if st.button("Toggle Sidebar", key="toggle_sidebar"):
        st.session_state.sidebar_visible = not st.session_state.sidebar_visible
        st.rerun()

with col2:
    st.title("NYC Zoning Assistant")

with col3:
    if st.button("New Chat", key="new_chat_btn"):
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

# Layout: Sidebar and main area
if st.session_state.sidebar_visible:
    sidebar_col, main_col = st.columns([3, 9])
else:
    main_col = st.container()
    sidebar_col = None

# Sidebar for conversation list
if sidebar_col is not None:
    with sidebar_col:
        st.header("Conversations")
        
        chats = st.session_state.chats
        if chats:
            sorted_chats = sorted(
                chats.items(),
                key=lambda x: last_message_timestamp(x[1]),
                reverse=True,
            )
            
            for chat_id, messages in sorted_chats:
                if messages:
                    first_user = next((m for m in messages if m.get("role") == "user"), None)
                    if first_user:
                        title_text = first_user["content"]
                    else:
                        title_text = "Untitled"
                    if len(title_text) > 50:
                        title = title_text[:50] + "..."
                    else:
                        title = title_text
                else:
                    title = "New conversation"
                
                is_active = chat_id == st.session_state.current_chat_id
                button_label = title
                
                if st.button(button_label, key=f"chat_{chat_id}", use_container_width=True):
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
        else:
            st.caption("No conversations yet. Start a new chat to begin.")
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This assistant provides expert answers about:
        - Zoning districts and regulations
        - Permitted uses and bulk requirements
        - Zoning procedures and compliance
        - Flood zones and design requirements
        - City planning policies
        """)
        
        st.markdown("---")
        st.markdown("### Quick Tips")
        st.markdown("""
        - Ask specific questions for best results
        - Use **address:** prefix for location lookups
        - Examples:
          - "What is a C1 zone?"
          - "address: 123 Main St, Manhattan"
          - "What are the bulk regulations for R6?"
        """)

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
    else:
        st.info("Start a conversation by asking a question about NYC zoning regulations.")
        st.markdown("""
        **Example questions:**
        - What are the zoning districts in Manhattan?
        - Explain the regulations for an R6 district.
        - What uses are allowed in a C1 commercial district?
        """)
    
    # Chat input
    prompt = st.chat_input("Type your question about NYC zoning...")
    
    if prompt:
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
