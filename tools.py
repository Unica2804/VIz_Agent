from google.adk.tools import ToolContext
async def read_uploaded_file(filename: str, tool_context: ToolContext) -> str:
    """
    Reads the content of a file stored in the Artifact Service.
    Args:
        filename: The name of the file to read.
    """
    # Access the shared artifact storage
    artifact = await tool_context.load_artifact(filename)
    
    if not artifact:
        return f"Error: I could not find a file named '{filename}' in storage."
    
    # Assuming text file for this demo. 
    try:
        content = artifact.inline_data.data.decode("utf-8")
        return f"Content of {filename}:\n{content[:2000]}" # Limit characters for demo
    except Exception as e:
        return f"Error decoding file: {str(e)}"