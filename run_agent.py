import asyncio
import os
# Add InMemoryArtifactService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from agents.Orchestrator import root_agent 

async def main():
    # 1. Setup Services
    session_service = InMemorySessionService()
    # Initialize Artifact Service explicitly
    artifact_service = InMemoryArtifactService() 
    
    # Constants for the session
    APP_NAME = "data_analysis_app"
    USER_ID = "developer"
    SESSION_ID = "test_session_01"

    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    # 2. Initialize Runner with the Artifact Service
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
        artifact_service=artifact_service  # <--- Pass this here
    )

    query_text = "Parse the file './data/sample.csv', get the statistics of the dataset."
    print(f"\n🔹 User Query: {query_text}\n")

    # 3. Run and Listen for Artifacts
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=types.Content(role="user", parts=[types.Part(text=query_text)])
    ):
        # ... (Keep your existing print statements for tool calls/code) ...

        # --- NEW: Handle Artifacts ---
        # Check if the event indicates an artifact was saved/updated
        if event.actions and event.actions.artifact_delta:
            for filename, version in event.actions.artifact_delta.items():
                print(f"\n📂 [Artifact Detected]: {filename} (Version {version})")
                
                # Retrieve the binary data from the service
                artifact_part = await artifact_service.load_artifact(
                    app_name=APP_NAME,
                    user_id=USER_ID,
                    session_id=SESSION_ID,
                    filename=filename
                )
                
                # Save it to your local disk
                if artifact_part and artifact_part.inline_data:
                    output_path = f"./output/{filename}"
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    with open(output_path, "wb") as f:
                        f.write(artifact_part.inline_data.data)
                    
                    print(f"   ✅ Saved locally to: {output_path}")

        # Print the Final Response
        if event.is_final_response():
            print(f"\n🤖 [Final Response]:\n{event.content.parts[0].text}\n")

if __name__ == "__main__":
    # ... (Keep your existing CSV creation logic) ...
    asyncio.run(main())