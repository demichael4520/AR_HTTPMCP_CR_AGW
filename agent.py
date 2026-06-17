import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams

# Define the MCP toolset connecting to the remote server
mcp_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://mcp-weather-server-431967288103.us-east1.run.app/mcp",
    )
)

# Define the root agent
root_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='mcp_weather_client',
    instruction='You are a helpful assistant that can check weather using tools.',
    tools=[mcp_toolset],
)
