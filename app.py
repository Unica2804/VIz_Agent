from agents import get_agent_response
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
import streamlit as st
import asyncio
from dotenv import load_dotenv

# --- Load environment variables ---

load_dotenv()

# ---  Constants and Configuration ---
APP_NAME = "streamlit_agent_app"
USER_ID = "streamlit_user"
SESSION_ID = "session_001"


# ---  Streamlit UI Logic ---

st.set_page_config(page_title="ADK Data Analyst", layout="wide")
st.title("🤖 ADK Data Analyst")

# Initialize ADK Services in Streamlit Session State (Persistent across reruns)
if 'adk_services' not in st.session_state:
    st.session_state['adk_services'] = {
        'session': InMemorySessionService(),
        'artifact': InMemoryArtifactService() # Stores files and generated plots in memory
    }
    # Create the session once
    asyncio.run(st.session_state['adk_services']['session'].create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    ))

# Sidebar for File Upload
with st.sidebar:
    st.header("📁 Upload Data")
    uploaded_file = st.file_uploader("Drag and drop a text file here", type=['txt', 'md', 'csv', 'py'])

# Chat Interface initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history (Text AND Images)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # If this message has associated images, display them
        if "images" in message:
            for img in message["images"]:
                st.image(
                    img["data"], 
                    caption=f"Generated Plot: {img['name']}", 
                    use_container_width=True
                )

# Chat Input
if prompt := st.chat_input("Ask something about the file..."):
    
    # 1. Display user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Prepare file info if a file exists
    file_data = None
    if uploaded_file:
        # We pass the file data to the backend logic to ensure it's saved in ADK
        file_data = (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
        
        # --- FIX: Aggressively hint the filename ---
        # If the user has a file uploaded, we tell the agent about it in the prompt
        # regardless of whether they typed the word "file".
        if uploaded_file.name not in prompt:
            prompt += f"\n(System Note: The user has an active file uploaded named '{uploaded_file.name}'.)"

    # 3. Get Agent Response
    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking..."):
            # Run the async ADK logic
            # Unpack response text AND images
            response_text, images = asyncio.run(
                get_agent_response(prompt, st.session_state['adk_services'], file_data)
            )
            
            # Render Text
            st.markdown(response_text)
            
            # Render Generated Images             
            for img in images:
                st.image(
                    img["data"], 
                    caption=f"Generated Plot: {img['name']}", 
                    use_container_width=True
                )
            
    # Save to chat history with images
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response_text,
        "images": images 
    })