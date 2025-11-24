from google.adk.tools import ToolContext
from google.genai import types


async def save_artifact(tool_context:ToolContext, content:str, filename: str):
    data_bytes = content.encode('utf-8')
    artifact_part=types.part(
        inline_data=types.Blob(mime_type='image/png', data=data_bytes)
    )
    await tool_context.artifact_manager.save_artifact(filename, artifact_part)
