# app.py
import streamlit as st
from query import get_answer
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="NYC Zoning Assistant",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern chat styling
st.markdown("""
    <style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        padding: 1rem 0;
    }
    
    /* Chat message styling */
    .chat-message {
        display: flex;
        margin-bottom: 1.5rem;
        padding: 1rem;
        border-radius: 10px;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 20%;
        justify-content: flex-end;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        color: #333;
        margin-right: 20%;
        border-left: 4px solid #1f77b4;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    .assistant-message .stMarkdown {
        margin-top: 0.5rem;
    }
    
    .assistant-message p {
        margin: 0.5rem 0;
    }
    
    .message-content {
        flex: 1;
        line-height: 1.6;
    }
    
    .message-role {
        font-weight: 600;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
        opacity: 0.8;
    }
    
    .stTextInput > div > div > input {
        border-radius: 25px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #1f77b4;
        box-shadow: 0 0 0 3px rgba(31, 119, 180, 0.1);
    }
    
    .stButton > button {
        border-radius: 25px;
        background: linear-gradient(90deg, #1f77b4, #2c8fd0);
        color: white;
        font-weight: 600;
        padding: 0.75rem 2rem;
        border: none;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #2c8fd0, #1f77b4);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(31, 119, 180, 0.3);
    }
    
    .chat-container {
        max-height: calc(100vh - 300px);
        overflow-y: auto;
        padding: 1rem 0;
    }
    
    .chat-container::-webkit-scrollbar {
        width: 8px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 10px;
    }
    
    .chat-container::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    
    .new-chat-btn {
        background: linear-gradient(90deg, #667eea, #764ba2) !important;
    }
    
    .chat-item {
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
        border: 1px solid transparent;
    }
    
    .chat-item:hover {
        background: #f0f8ff;
        border-color: #1f77b4;
    }
    
    .chat-item.active {
        background: #e8f4f8;
        border-color: #1f77b4;
        font-weight: 600;
    }
    
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: #666;
    }
    
    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for chat management
if 'chats' not in st.session_state:
    st.session_state.chats = {}  # {chat_id: [{"role": "user"/"assistant", "content": "...", "timestamp": "..."}]}
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = None
if 'chat_counter' not in st.session_state:
    st.session_state.chat_counter = 0

# Header
st.markdown('<h1 class="main-header">🏙️ NYC Zoning Assistant</h1>', unsafe_allow_html=True)

# Sidebar for chat history
with st.sidebar:
    st.markdown("### 💬 Chat History")
    
    # New Chat button
    if st.button("➕ New Chat", use_container_width=True, type="primary", key="new_chat_btn"):
        st.session_state.chat_counter += 1
        st.session_state.current_chat_id = f"chat_{st.session_state.chat_counter}"
        st.session_state.chats[st.session_state.current_chat_id] = []
        st.rerun()
    
    st.markdown("---")
    
    # Display chat history
    if st.session_state.chats:
        # Sort chats by most recent (by last message timestamp)
        sorted_chats = sorted(
            st.session_state.chats.items(),
            key=lambda x: x[1][-1]["timestamp"] if x[1] else datetime.min,
            reverse=True
        )
        
        for chat_id, messages in sorted_chats:
            # Get chat title from first user message
            chat_title = "New Chat"
            if messages:
                first_user_msg = next((msg for msg in messages if msg["role"] == "user"), None)
                if first_user_msg:
                    chat_title = first_user_msg["content"][:50] + ("..." if len(first_user_msg["content"]) > 50 else "")
            
            # Display chat item
            is_active = chat_id == st.session_state.current_chat_id
            button_label = f"💬 {chat_title}"
            
            if st.button(button_label, key=f"chat_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.rerun()
    else:
        st.info("No chats yet. Start a new conversation!")
    
    st.markdown("---")
    st.markdown("### 📚 About")
    st.markdown("""
    This assistant provides expert answers about:
    - Zoning districts and regulations
    - Permitted uses and bulk requirements
    - Zoning procedures and compliance
    - Flood zones and design requirements
    - City planning policies
    """)
    
    st.markdown("---")
    st.markdown("### 💡 Quick Tips")
    st.markdown("""
    - Ask specific questions for best results
    - Use **address:** prefix for location lookups
    - Examples:
      - "What is a C1 zone?"
      - "address: 123 Main St, Manhattan"
      - "What are the bulk regulations for R6?"
    """)

# Main chat area
if st.session_state.current_chat_id is None:
    # Create first chat if none exists
    st.session_state.chat_counter += 1
    st.session_state.current_chat_id = f"chat_{st.session_state.chat_counter}"
    st.session_state.chats[st.session_state.current_chat_id] = []

# Get current chat messages
current_chat = st.session_state.chats.get(st.session_state.current_chat_id, [])

# Display chat messages
import html

chat_container = st.container()
with chat_container:
    if current_chat:
        for msg in current_chat:
            role = msg["role"]
            content = msg["content"]
            
            if role == "user":
                # User message - right aligned
                col1, col2 = st.columns([3, 7])
                with col1:
                    st.write("")  # Spacer
                with col2:
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <div class="message-content">
                            <div class="message-role">👤 You</div>
                            <div>{html.escape(content).replace(chr(10), '<br>')}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:  # assistant
                # Assistant message - left aligned
                col1, col2 = st.columns([7, 3])
                with col1:
                    st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <div class="message-content">
                            <div class="message-role">🤖 Assistant</div>
                    """, unsafe_allow_html=True)
                    # Render markdown using Streamlit's native renderer
                    st.markdown(content)
                    st.markdown("""
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.write("")  # Spacer
    else:
        # Empty state
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">🏙️</div>
            <h2>Welcome to NYC Zoning Assistant!</h2>
            <p>Ask me anything about NYC zoning regulations, districts, and land use.</p>
            <p style="margin-top: 2rem; color: #999;">Try asking:</p>
            <ul style="text-align: left; display: inline-block; color: #999;">
                <li>"What are the different zoning districts?"</li>
                <li>"What is a C1 commercial zone?"</li>
                <li>"What are the bulk regulations for R6?"</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# Input area (sticky at bottom)
st.markdown("---")

# Use form for better UX
with st.form(key="chat_form", clear_on_submit=True):
    col_input, col_submit = st.columns([5, 1])
    
    with col_input:
        user_input = st.text_input(
            "Type your message...",
            placeholder="Ask about NYC zoning regulations...",
            key="user_input",
            label_visibility="collapsed"
        )
    
    with col_submit:
        submit_button = st.form_submit_button("Send 🚀", use_container_width=True)

# Handle message submission
if submit_button and user_input:
    # Add user message to chat
    user_msg = {
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().isoformat()
    }
    current_chat.append(user_msg)
    st.session_state.chats[st.session_state.current_chat_id] = current_chat
    
    # Get assistant response
    with st.spinner("🔍 Searching zoning documents and analyzing..."):
        try:
            answer = get_answer(user_input)
            
            # Add assistant message to chat
            assistant_msg = {
                "role": "assistant",
                "content": answer,
                "timestamp": datetime.now().isoformat()
            }
            current_chat.append(assistant_msg)
            st.session_state.chats[st.session_state.current_chat_id] = current_chat
            
            st.rerun()
            
        except Exception as e:
            error_msg = {
                "role": "assistant",
                "content": f"❌ Error: {str(e)}\n\nPlease try again or rephrase your question.",
                "timestamp": datetime.now().isoformat()
            }
            current_chat.append(error_msg)
            st.session_state.chats[st.session_state.current_chat_id] = current_chat
            st.rerun()

# Footer info
st.markdown("""
<div style="text-align: center; padding: 1rem; color: #666; font-size: 0.9rem;">
    <strong>ℹ️ Note:</strong> This assistant uses official NYC zoning documentation to provide accurate, 
    authoritative answers. For legal matters, always consult with a licensed professional.
</div>
""", unsafe_allow_html=True)
