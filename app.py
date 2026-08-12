from agents import get_agent_response
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
import streamlit as st
import asyncio
from dotenv import load_dotenv
from google.genai.errors import ClientError
import uuid
import time


def _safe_rerun():
    """Call Streamlit rerun compatibly across versions.

    Prefers `st.rerun()` if present, falls back to `st.experimental_rerun()` or `st.stop()`.
    """
    if hasattr(st, "rerun"):
        try:
            st.rerun()
            return
        except Exception:
            pass
    if hasattr(st, "experimental_rerun"):
        try:
            st.experimental_rerun()
            return
        except Exception:
            pass
    # Best-effort fallback
    st.stop()

# --- Load environment variables ---

load_dotenv()

# ---  Constants and Configuration ---
APP_NAME = "streamlit_agent_app"
USER_ID = "streamlit_user"
# Default session id (legacy initial session id)
DEFAULT_SESSION_ID = "session_001"


# ---  Streamlit UI Logic ---

st.set_page_config(page_title="ADK Data Analyst", layout="wide")
st.title("🤖 ADK Data Analyst")

# Initialize ADK Services in Streamlit Session State (Persistent across reruns)
if 'adk_services' not in st.session_state:
    st.session_state['adk_services'] = {
        'session': InMemorySessionService(),
        'artifact': InMemoryArtifactService() 
    }
    # Create the initial session once and store it in session state
    asyncio.run(st.session_state['adk_services']['session'].create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=DEFAULT_SESSION_ID
    ))
    st.session_state['session_id'] = DEFAULT_SESSION_ID
    st.session_state['sessions'] = {}  # session_id -> {messages, created_at}
    st.session_state['viewing_session'] = None

# Sidebar for File Upload
with st.sidebar:
    st.header("📁 Upload Data")
    uploaded_file = st.file_uploader("Drag and drop a text file here", type=['txt', 'md', 'csv', 'py'])
    st.markdown("---")
    # New Chat button: create new session and move current messages into session history
    if st.button("+ New Chat"):
        current_sid = st.session_state.get('session_id', DEFAULT_SESSION_ID)
        # Save the current session messages if there are messages
        if st.session_state.get('messages'):
            st.session_state['sessions'][current_sid] = {
                'id': current_sid,
                'messages': st.session_state['messages'].copy(),
                'created_at': time.time()
            }
        # Create new session id
        new_sid = f"session_{uuid.uuid4().hex[:8]}"
        asyncio.run(st.session_state['adk_services']['session'].create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=new_sid
        ))
        st.session_state['session_id'] = new_sid
        st.session_state['messages'] = []
        st.session_state['viewing_session'] = None
        _safe_rerun()

    st.markdown("### Chat History")
    # Render session history. Most recent first
    sessions_sorted = sorted(st.session_state.get('sessions', {}).items(), key=lambda x: x[1]['created_at'], reverse=True)
    for sid, sdata in sessions_sorted:
        cols = st.columns([1, 1])
        # View button shows the session messages in the main pane
        if cols[0].button(f"View {sid}"):
            st.session_state['viewing_session'] = sid
            _safe_rerun()
        # Load button makes this session the active session (so user can continue chat)
        if cols[1].button(f"Load {sid}"):
            st.session_state['session_id'] = sid
            st.session_state['messages'] = st.session_state['sessions'][sid]['messages'].copy()
            st.session_state['viewing_session'] = None
            _safe_rerun()

# Chat Interface initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history (Text AND Images)
display_messages = st.session_state.messages
if st.session_state.get('viewing_session'):
    # Show messages for the selected historic session in read-only mode
    display_messages = st.session_state['sessions'].get(st.session_state['viewing_session'], {}).get('messages', [])

for message in display_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "images" in message:
            for img in message["images"]:
                st.image(
                    img["data"], 
                    caption=f"Generated Plot: {img['name']}", 
                    use_container_width=True
                )

# Chat Input
if st.session_state.get('viewing_session'):
    st.info(
        f"Viewing past session: {st.session_state['viewing_session']}. Click Load to resume this session or + New Chat to start another."
    )
else:
    if prompt := st.chat_input("Ask something about the file..."):
        # Validate prompt - must be non-empty and not just whitespace
        if not prompt or not prompt.strip():
            st.warning("Please enter a non-empty message.")
        else:
            # Display user message
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Prepare file info if a file exists
            file_data = None
            if uploaded_file:
                # We pass the file data to the backend logic to ensure it's saved in ADK
                file_data = (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                # Optionally, inform the agent about the uploaded file in the prompt
                if uploaded_file.name not in prompt:
                    prompt += f"\n(System Note: The user has an active file uploaded named '{uploaded_file.name}'.)"

            # Get Agent Response
            with st.chat_message("assistant"):
                with st.spinner("Agent is thinking..."):
                    # Run the async ADK logic
                    # Unpack response text AND images
                    try:
                        response_text, images = asyncio.run(
                            get_agent_response(
                                prompt,
                                st.session_state['adk_services'],
                                file_data,
                                session_id=st.session_state.get('session_id', DEFAULT_SESSION_ID),
                            )
                        )
                    except ClientError as e:
                        err_msg = str(e)
                        st.error(f"AI API error: {err_msg}")
                        response_text = f"AI API error: {err_msg}"
                        images = []
                    except Exception as e:
                        # Provide a user-friendly message and rethrow for logs if needed
                        err_msg = str(e)
                        st.error(f"Error: {err_msg}")
                        # Write to messages in UI as well
                        response_text = f"Internal error: {err_msg}"
                        images = []

                    # Render Text
                    st.markdown(response_text)

                    # Render Generated Images
                    for img in images:
                        st.image(
                            img["data"],
                            caption=f"Generated Plot: {img['name']}",
                            use_container_width=True,
                        )

                    # Save to chat history with images
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "images": images,
                    })