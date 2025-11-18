# app.py
import streamlit as st
from datetime import datetime
import html

from query import get_answer


# ---------- Helpers ----------
def normalize_timestamp(ts):
    """Return a datetime for any timestamp value (str/datetime/None)."""
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        # Adjust this format if you store timestamps differently
        try:
            return datetime.fromisoformat(ts)
        except ValueError:
            pass
    return datetime.min


def last_message_timestamp(messages):
    """Safely get the last message timestamp from a chat."""
    if not messages:
        return datetime.min
    # use last element; fall back if 'timestamp' is missing
    ts = messages[-1].get("timestamp") if isinstance(messages[-1], dict) else None
    return normalize_timestamp(ts)


# ---------- Page config ----------
st.set_page_config(
    page_title="NYC Zoning Assistant",
    page_icon=None,
    layout="wide",
)

# ---------- Custom CSS ----------
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    body { background-color: #f4f5f7; }

    .app-header {
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #e2e4e8;
        background-color: #ffffff;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .app-title {
        font-size: 1.2rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    }

    .header-button > button {
        border-radius: 999px;
        padding: 0.35rem 0.9rem;
        font-size: 0.85rem;
    }

    .sidebar-panel {
        background-color: #ffffff;
        border-right: 1px solid #e2e4e8;
        height: calc(100vh - 56px);
        padding: 0.75rem;
        overflow-y: auto;
    }

    .sidebar-title {
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .chat-list-item {
        padding: 0.6rem 0.7rem;
        border-radius: 6px;
        border: 1px solid transparent;
        font-size: 0.85rem;
        margin-bottom: 0.3rem;
        cursor: pointer;
        background-color: #f7f8fa;
    }

    .chat-list-item.active {
        border-color: #2563eb;
        background-color: #eff3ff;
        font-weight: 500;
    }

    .chat-list-item-title {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .chat-main {
        height: calc(100vh - 56px);
        padding: 0.75rem 1.5rem 0;
        display: flex;
        flex-direction: column;
    }

    .chat-scroll {
        flex: 1;
        overflow-y: auto;
        padding-bottom: 1rem;
    }

    .empty-state {
        color: #7b7d82;
        text-align: center;
        margin-top: 4rem;
    }

    .empty-state h3 {
        font-weight: 500;
        margin-bottom: 0.5rem;
    }

    .empty-state ul {
        margin-top: 0.75rem;
        padding-left: 1.1rem;
        text-align: left;
        display: inline-block;
        color: #9a9da3;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Session state ----------
if "chats" not in st.session_state:
    # {chat_id: [{"role": "user"/"assistant", "content": str, "timestamp": iso_str}]}
    st.session_state.chats = {}

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "chat_counter" not in st.session_state:
    st.session_state.chat_counter = 0

if "show_sidebar" not in st.session_state:
    st.session_state.show_sidebar = True


# ---------- Header ----------
with st.container():
    col_menu, col_title, col_right = st.columns([1, 6, 2])

    with col_menu:
        st.markdown('<div class="app-header">', unsafe_allow_html=True)
        if st.button("Sidebar", key="toggle_sidebar", help="Show or hide conversations"):
            st.session_state.show_sidebar = not st.session_state.show_sidebar
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_title:
        st.markdown(
            '<div class="app-header"><div class="app-title">NYC Zoning Assistant</div></div>',
            unsafe_allow_html=True,
        )

    with col_right:
        st.markdown('<div class="app-header header-button">', unsafe_allow_html=True)
        if st.button("New chat", key="new_chat_btn"):
            st.session_state.chat_counter += 1
            new_id = f"chat_{st.session_state.chat_counter}"
            st.session_state.chats[new_id] = []
            st.session_state.current_chat_id = new_id
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# Ensure we always have a current chat
if st.session_state.current_chat_id is None:
    st.session_state.chat_counter += 1
    first_id = f"chat_{st.session_state.chat_counter}"
    st.session_state.chats[first_id] = []
    st.session_state.current_chat_id = first_id

# ---------- Layout: sidebar + main ----------
if st.session_state.show_sidebar:
    sidebar_col, main_col = st.columns([3, 9])
else:
    main_col = st.container()
    sidebar_col = None

# ----- Sidebar: conversation list -----
if sidebar_col is not None:
    with sidebar_col:
        st.markdown('<div class="sidebar-panel">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">Conversations</div>', unsafe_allow_html=True)

        chats = st.session_state.chats
        if chats:
            # ✅ SAFE sort using normalized timestamps
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
                    if len(title_text) > 60:
                        title = title_text[:60] + "..."
                    else:
                        title = title_text
                else:
                    title = "New conversation"

                is_active = chat_id == st.session_state.current_chat_id
                css_class = "chat-list-item active" if is_active else "chat-list-item"

                with st.container():
                    st.markdown(
                        f'<div class="{css_class}"><div class="chat-list-item-title">{html.escape(title)}</div></div>',
                        unsafe_allow_html=True,
                    )
                    if st.button("Open", key=f"open_{chat_id}", use_container_width=True):
                        st.session_state.current_chat_id = chat_id
                        st.rerun()
        else:
            st.caption("No conversations yet.")

        st.markdown("</div>", unsafe_allow_html=True)

# ---------- Main chat area ----------
with main_col:
    st.markdown('<div class="chat-main">', unsafe_allow_html=True)

    current_chat = st.session_state.chats.get(st.session_state.current_chat_id, [])

    st.markdown('<div class="chat-scroll">', unsafe_allow_html=True)
    if current_chat:
        for msg in current_chat:
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            with st.chat_message(role):
                st.markdown(content)
    else:
        st.markdown(
            """
            <div class="empty-state">
                <h3>Start a conversation</h3>
                <p>Ask questions about NYC zoning regulations, districts and land use.</p>
                <ul>
                    <li>What are the zoning districts in Manhattan?</li>
                    <li>Explain the regulations for an R6 district.</li>
                    <li>What uses are allowed in a C1 commercial district?</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Chat input (bottom, ChatGPT style)
    prompt = st.chat_input("Type your question about NYC zoning…")

    if prompt:
        # store + show user message
        user_msg = {
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat(),
        }
        current_chat.append(user_msg)
        st.session_state.chats[st.session_state.current_chat_id] = current_chat

        with st.chat_message("user"):
            st.markdown(prompt)

        # assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
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
