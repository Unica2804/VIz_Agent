from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from tools import read_uploaded_file
from google.adk.tools import AgentTool
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.models.google_llm import Gemini
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "streamlit_agent_app"
USER_ID = "streamlit_user"
SESSION_ID = "session_001"

async def get_agent_response(prompt, services, file_info=None):
    """Runs the ADK Agent loop."""
    
    # Define Agent
    retry_config = types.HttpRetryOptions(attempts=3, initial_delay=1)

    # Coder Agent
    coder_agent = LlmAgent(
        name="coder_agent",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        # The built-in executor will save generated plots as artifacts
        code_executor=BuiltInCodeExecutor(),
        description="Agent specialized in generating python code",
        instruction="""
            You are an expert Python Developer. Your role is to write and execute code to solve data problems.

            1. **Data Loading**: 
            - If you are given the text content of a file, use `io.StringIO` to load it into a pandas DataFrame.
            - If you are given just a filename, assume it exists in the current directory and load it directly (e.g., `pd.read_csv()`).
            2. **Execution**: Use the code executor to run your code immediately.
            3. **Plotting**: When asked to plot, use `matplotlib.pyplot`. Ensure you generate the figure so it can be captured by the system.
            4. **Output**: Print the final result (e.g., the statistics dataframe or quality checks) to standard output so it can be read.
        """,
    )

    # Stats Agent
    stats_agent = LlmAgent(
        name="Stats_Agent",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        description="Computes descriptive statistics.",
        instruction="""
            You are a Senior Quantitative Analyst. Your goal is to provide a comprehensive statistical health check of data files.

            1. **Retrieve Data**: IF a filename is provided, you MUST FIRST call the tool `read_uploaded_file` to get the file content.
            2. **Delegate Analysis**: Call `coder_agent` to load the data and perform the analysis.
            - **Default Comprehensive Analysis**: Unless the user asks for a specific metric, you MUST instruct the coder to calculate ALL of the following for numeric columns:
                - Central Tendency: Mean, Median, Mode
                - Dispersion: Min, Max, Std Dev, Variance, Quartiles (Q1/Q3), IQR
                - Data Quality: Count, Missing Value Counts
                - Relationships: Correlation Matrix (only if there are 2 or more numeric columns)
            - **Validation**: Instruct the coder to explicitly check for and report skewness, potential outliers, and any data-quality issues (e.g., high missing values).
            3. **Report**: Return a detailed text summary of these metrics and any quality flags raised.
        """,
        tools=[AgentTool(coder_agent), read_uploaded_file],
    )

    # Visualization Agent
    visualization_agent = LlmAgent(
        name="Visualization_Agent",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        description="Generates visual explanations.",
        instruction="""
            You are a Data Visualization Specialist. Your goal is to create clear and meaningful charts.

            1. **Retrieve Data**: IF a filename is provided, you MUST FIRST call the tool `read_uploaded_file` to get the file context.
            2. **Delegate Plotting**: Call `coder_agent` to generate the code for the plot.
            - Be specific about the plot type (scatter, line, bar, histogram).
            - Instruct the coder to use `matplotlib` or `seaborn` or `plotly` .
            - Ensure the coder adds a title, x-label, and y-label to the plot.
        """,
        tools=[AgentTool(coder_agent), read_uploaded_file], 
    )

    # Root Orchestrator
    root_agent = LlmAgent(
        name="Orchestrator",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        description="Routes user intents.",
        instruction="""
            You are the Lead Coordinator of a data analysis team. Your sole responsibility is to route user requests to the correct specialist agent.

            1. **Analyze** the user's intent:
            - If the user wants to *understand* the data (e.g., "describe", "summary", "analyze", "statistics", "check data quality"), delegate to **Stats_Agent**.
            - If the user wants to *see* the data (e.g., "plot", "chart", "graph", "visualize"), delegate to **Visualization_Agent**.

            2. **Pass Context**: If the user mentions a filename, ensure you pass that filename clearly to the sub-agent so they know which file to process.
        """,
        sub_agents=[stats_agent, visualization_agent],
    )

    # Initialize Runner with the SHARED artifact service
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=services['session'],
        artifact_service=services['artifact'] 
    )

    # If a file was just uploaded, save it to ADK Artifact Service
    if file_info:
        file_name, file_bytes, mime_type = file_info
        
        # Create ADK artifact object
        artifact_part = types.Part(
            inline_data=types.Blob(
                mime_type=mime_type,
                data=file_bytes
            )
        )
        
        # Save to the centralized service
        await services['artifact'].save_artifact(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID,
            filename=file_name,
            artifact=artifact_part
        )

    # Create user message
    user_msg = types.Content(role="user", parts=[types.Part(text=prompt)])

    response_text = ""
    generated_images = [] # List to hold image data found during execution

    # Run Agent Loop
    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=user_msg):
        
        # 1. Check for Artifacts (Plots) saved during this step
        if event.actions and event.actions.artifact_delta:
            for filename in event.actions.artifact_delta:
                # Simple check for image files
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    # Load the actual bytes from the service
                    artifact = await services['artifact'].load_artifact(
                        app_name=APP_NAME,
                        user_id=USER_ID,
                        session_id=SESSION_ID,
                        filename=filename
                    )
                    
                    if artifact and artifact.inline_data:
                        generated_images.append({
                            "name": filename,
                            "data": artifact.inline_data.data, # Raw bytes
                            "mime_type": artifact.inline_data.mime_type
                        })

        # 2. Check for Final Text Response
        if event.is_final_response():
            if event.content and event.content.parts:
                response_text = event.content.parts[0].text
            
    return response_text, generated_images