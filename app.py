# app.py
import streamlit as st
from datetime import datetime

from query import get_answer


# ---------- Helper functions ----------

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


# ---------- Page configuration & CSS ----------

st.set_page_config(
    page_title="NYC Zoning Assistant",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    /* Main page padding */
    .main {
        padding-top: 1.5rem;
    }

    /* Header layout tweaks */
    .header-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
    }
    .header-title {
        flex: 1;
        text-align: center;
    }
    .header-buttons {
        display: flex;
        gap: 0.5rem;
    }

    /* Make icon buttons roundish and compact */
    .stButton > button {
        border-radius: 999px;
        padding: 0.35rem 0.8rem;
        font-size: 1.1rem;
        line-height: 1;
    }

    /* Mobile: stack header elements */
    @media (max-width: 768px) {
        .header-row {
            flex-direction: column;
        }
        .header-title {
            text-align: center;
            width: 100%;
        }
        .header-buttons {
            justify-content: center;
            width: 100%;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Session state ----------

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

# Rotate placeholder every few reruns (when idle)
st.session_state.rerun_count += 1
if st.session_state.rerun_count % 5 == 0:
    st.session_state.placeholder_index = (
        st.session_state.placeholder_index + 1
    ) % len(example_questions)

current_placeholder = example_questions[
    st.session_state.placeholder_index % len(example_questions)
]

# ---------- Header (icons + centered title + expanders) ----------

header_container = st.container()
with header_container:
    st.markdown('<div class="header-row">', unsafe_allow_html=True)

    # Left: sidebar toggle
    toggle_col, title_col, actions_col = st.columns([1, 6, 1])

    with toggle_col:
        if st.button("☰", key="toggle_sidebar", help="Show / hide conversations"):
            st.session_state.sidebar_visible = not st.session_state.sidebar_visible
            st.rerun()

    with title_col:
        st.markdown(
            '<h1 class="header-title">NYC Zoning Assistant</h1>',
            unsafe_allow_html=True,
        )

        # About & Quick Tips under title
        with st.expander("About", expanded=False):
            st.markdown(
                """
                This assistant helps you understand NYC zoning by answering questions about:
                - Zoning districts and regulations  
                - Permitted uses and bulk requirements  
                - Zoning procedures and compliance  
                - Flood zones and design requirements  
                - City planning policies and related concepts  
                """
            )

        with st.expander("Quick Tips", expanded=False):
            st.markdown(
                """
                - Ask specific questions for the best answers  
                - Examples:  
                  - *"What is a C1 zone?"*  
                  - *"Where are commercial overlays allowed?"*  
                  - *"What are the bulk regulations for R6?"*  
                """
            )

    with actions_col:
        # Right: new chat icon
        if st.button("＋", key="new_chat_btn", help="Start a new conversation"):
            st.session_state.chat_counter += 1
            new_id = f"chat_{st.session_state.chat_counter}"
            st.session_state.chats[new_id] = []
            st.session_state.current_chat_id = new_id
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Ensure at least one chat exists ----------

if st.session_state.current_chat_id is None:
    st.session_state.chat_counter += 1
    first_id = f"chat_{st.session_state.chat_counter}"
    st.session_state.chats[first_id] = []
    st.session_state.current_chat_id = first_id

# ---------- Layout: sidebar + main ----------

if st.session_state.sidebar_visible:
    sidebar_col, main_col = st.columns([2, 8])
else:
    main_col = st.container()
    sidebar_col = None

# Sidebar: conversation list
if sidebar_col is not None:
    with sidebar_col:
        st.subheader("Conversations")

        chats = st.session_state.chats
        chats_with_messages = {k: v for k, v in chats.items() if v}

        if chats_with_messages:
            sorted_chats = sorted(
                chats_with_messages.items(),
                key=lambda x: last_message_timestamp(x[1]),
                reverse=True,
            )

            for chat_id, messages in sorted_chats:
                first_user = next(
                    (m for m in messages if m.get("role") == "user"), None
                )
                if first_user:
                    title_text = first_user["content"]
                else:
                    title_text = "Untitled"

                title = (
                    title_text[:40] + "..." if len(title_text) > 40 else title_text
                )
                is_active = chat_id == st.session_state.current_chat_id

                # Slightly emphasize active chat
                if st.button(
                    ("💬 " if is_active else "") + title,
                    key=f"chat_{chat_id}",
                    use_container_width=True,
                ):
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
        else:
            st.caption("No conversations yet. Click ＋ to start a new chat.")

# ---------- Main chat area ----------

with main_col:
    current_chat = st.session_state.chats.get(
        st.session_state.current_chat_id, []
    )

    # Existing messages
    if current_chat:
        for msg in current_chat:
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            with st.chat_message(role):
                st.markdown(content)

    # Input
    prompt = st.chat_input(current_placeholder)

    if prompt:
        st.session_state.rerun_count = 0

        # Store user message
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
