import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

# Define the MCP toolset connecting to the remote server
mcp_toolset = McpToolset(
    connection_params=SseConnectionParams(
        url="https://mcp-weather-server-579295505315.us-central1.run.app/sse",
    )
)

# Define the root agent
root_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='mcp_weather_client',
    instruction='You are a helpful assistant that can check weather using tools.',
    tools=[mcp_toolset],
)
