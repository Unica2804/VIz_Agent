from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool,ToolContext
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.models.google_llm import Gemini
from google.genai import types
from .tools.data_extractor import data_parser
from ..utils.artifact import save_artifact
from dotenv import load_dotenv

load_dotenv()

# Retry_config
retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

# Parser agent: Parses uploaded data and saves it into json. Then returns a dict containing metadata and location of stored json
Parser_agent = LlmAgent(
    name="File_Parser_Agent",
    model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
    description=""" 
        An agent that parses files and extracts information based on user queries.
    """,
    instruction= """ You are a File Parser Agent. Your task is to parse files
        and extract information using the provided tools based on user queries.
        tools:
        - data_parser: A tool that parses files and extracts structured data.
    """,
    tools=[data_parser],
)


# Coder Agent: Used for generating codes

coder_agent = LlmAgent(
    name="coder_agent",
    model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
    code_executor=BuiltInCodeExecutor(),
    description="Agent specialized in generating python code",
    instruction="""
        You are a coding specialist.
        Steps:
        1. Understand the user's request.
        2. Write python code to fulfill the request.
        3. Use the code executor to run the code and get results.
        4. If code execution fails, debug the code and retry once.
    """,
)

# Stats_agent: Calculates all the necessary statistics for a given data and returns the result

Stats_agent = LlmAgent(
    name="Stats_Agent",
    model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
    description="Computes descriptive statistics from structured data artifacts.",
    instruction="""
        You are a quantitative analyst.
        Workflow:
        1. Load the provided dataset (JSON/CSV/etc.) into pandas.
        2. Always compute visualization-friendly stats: count, mean, median, mode,
        min, max, std, variance, quartiles (Q1/Q3), IQR, missing counts, and
        correlation matrix when numeric columns >= 2.
        3. Serve user-specific metrics in addition to the defaults.
        4. Execute Python code using the tool - 'coder_agent'. Return only the output
        5. Validate assumptions, note skew/outliers, and flag data-quality issues.
    """,
    tools=[
        AgentTool(coder_agent)
    ]
)

# Visualization_Agent: It uses Coding agent to generate Plot's as per user query then saves them as artifact in the session

Visualization_agent = LlmAgent(
    name="Visualization_Agent",
    model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
    description="Generates visual explanations from structured datasets.",
    instruction="""
        You are a visualization specialist.
        Steps:
        1. Inspect the supplied dataset or stats output to understand fields.
        2. Plan charts (matplotlib/plotly/seaborn) matching the analytical goal.
        3. Run plotting code with the help of 'code_agent'
        4. You must save save results using 'save_artifact' tool to save file as an artifact with a filename.
        4. Describe the visualization, axes, and insights. If plotting fails, debug and retry once.
    """,
    tools=[
        AgentTool(coder_agent),
        save_artifact
    ]
)

# Orchestrator: The main agent that designates tasks to different sub_agents

root_agent = LlmAgent(
    name="Orchestrator",
    model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
    description="Routes user intents to parsing, statistics, or visualization tools.",
    instruction="""
        You are the coordinator.
        1. Interpret the user request and decide which tool(s) to call.
        2. Use the Parser tool for file ingestion and schema extraction.
        3. Use the Stats tool for descriptive analytics.
        4. Use the Visualization tool for chart generation.
        5. Chain multiple tool calls when needed
    """,
    sub_agents=[Parser_agent,Stats_agent,Visualization_agent],
)