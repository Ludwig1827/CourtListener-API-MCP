from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

import os
from openai import OpenAI
import json
from dotenv import load_dotenv

load_dotenv(override=True)


server_params = StdioServerParameters(
    command="mcp",
    args=["run", "server.py"],
    env=None,
)


def call_llm(prompt, functions):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    print("CALLING LLM")

    response = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful legal assistant that can call tools to perform tasks."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        tools=functions
    )

    response_message = response.choices[0].message

    functions_to_call = []
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            print("TOOL: ", tool_call)
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            functions_to_call.append({"name": name, "args": args})
    
    return functions_to_call



def convert_to_llm_tool(tool):
    # Add validation to ensure tool has required properties
    if not tool or not hasattr(tool, 'name') or not hasattr(tool, 'description'):
        print(f"Warning: Invalid tool, skipping: {tool}")
        return None
    
    # Handle missing inputSchema
    properties = {}
    if hasattr(tool, 'inputSchema') and tool.inputSchema and 'properties' in tool.inputSchema:
        properties = tool.inputSchema["properties"]
    
    tool_schema = {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": properties
            }
        }
    }
    return tool_schema

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # List available resources
            resources = await session.list_resources()
            print("LISTING RESOURCES")
            for resource in resources:
                print("Resource: ", resource)
            
            # List available tools
            tools = await session.list_tools()
            print("LISTING TOOLS")
            functions = []
            for tool in tools.tools:
                print("Tool: ", tool.name)
                print("Tool properties:", getattr(tool, 'inputSchema', {}).get('properties', {}))
                converted_tool = convert_to_llm_tool(tool)
                if converted_tool:  # Only add valid tools
                    functions.append(converted_tool)
            
            print(f"Valid functions count: {len(functions)}")
            
            # Only call LLM if we have valid functions
            if not functions:
                print("No valid tools found, skipping LLM call")
                return
            
            prompt = "I want to get some real cases of starting businesses with F-1 visa in the US. Can you help me with that? Please also give me the summary based on the opnion ID"
            # ask LLM what tools to call, if any
            functions_to_call = call_llm(prompt, functions)
            
            # call suggested functions
            for f in functions_to_call:
                result = await session.call_tool(f["name"], arguments=f["args"])
                print("TOOLS result: ", result.content)







if __name__ == "__main__":
    import asyncio

    asyncio.run(run())