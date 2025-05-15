import asyncio
import nest_asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

nest_asyncio.apply()  # Needed to run interactive python

"""
Make sure:
1. The server is running before running this script.
2. The server is configured to use SSE transport.
3. The server is listening on port 8050.

To run the server:
uv run server.py
"""
import ollama
async def main():
    # Connect to the server using SSE
    async with sse_client("http://localhost:8050/sse") as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            tools_result = await session.list_tools()
            print("Available tools:")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")

            # Convert MCP tools to Ollama-compatible format
            ollama_tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "The expression to calculate"
                            }
                        },
                        "required": ["expression"]
                    }
                } for tool in tools_result.tools
            ]
            client = ollama.AsyncClient()
            model_name = 'qwen3:1.7b'
            messages = [{'role': 'user', 'content': 'What is three plus one?'}]
            
            # Use the properly formatted tools
            response = await client.chat(
                model_name,
                messages=messages,
                tools=ollama_tools,  # Use the converted tools format
            )


            # Only needed to chat with the model using the tool call results
            if response.message.tool_calls:
                for tool_call in response.message.tool_calls:
                    # Extract tool name and arguments
                    tool_name = tool_call.function.name
                    tool_args = tool_call.function.arguments
                    
                    # Call the MCP tool with the arguments
                    output = await session.call_tool(tool_name, arguments=tool_args)
                    
                    # Add the function response to messages for the model to use
                    messages.append(response.message)
                    messages.append({'role': 'tool', 'content': str(output.content[0].text), 'name': tool_name})

                # Get final response from model with function outputs
                final_response = await client.chat(model_name, messages=messages)
                print( final_response.message.content)
            else:
                print(response.message.content)


if __name__ == "__main__":
    asyncio.run(main())