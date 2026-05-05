import json, os, sys, asyncio
from src.config import SERVERS_CONFIG_PATH

parent_dir = os.path.dirname(os.path.abspath(__file__))
grandparent_dir = os.path.dirname(parent_dir)
sys.path.append(grandparent_dir)

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.agent_graph import build_graph

def load_server_config():
    """Loads MCP server configuration from JSON file."""
    if not os.path.exists(SERVERS_CONFIG_PATH):
        print(f"Error: Server configuration not found at {SERVERS_CONFIG_PATH}")
        return {}
    with open(SERVERS_CONFIG_PATH, "r") as f:
        config = json.load(f)
        return config.get("mcpServers", {})

async def run_workflow(claim_id: int):
    """
    Runs the full insurance claim workflow for a given claim_id.
    """
    server_config = load_server_config()
    if not server_config:
        return

    print(f"🚀 Starting workflow for Claim ID: {claim_id}")
    
    async with MultiServerMCPClient(server_config) as client:
        tools = client.get_tools()
        print(f"🛠 Available tools: {[t.name for t in tools]}")
        
        graph = await build_graph(client)
        
        # Comprehensive instruction for the agent
        user_input = (
            f"Process claim {claim_id}: extract data, validate it, verify the policy, "
            f"check for fraud, and if everything is correct, process the payment and notify the underwriter. "
            f"If fraud is detected, stop and notify immediately."
        )

        async for event in graph.astream(
            {"messages": [HumanMessage(content=user_input)]}
        ):
            try:
                for node_name, value in event.items():
                    print(f"--- Node: {node_name} ---")
                    for message in value.get("messages", []):
                        if isinstance(message, ToolMessage):
                            print(f"Tool Result ({message.name}): {message.content[:200]}...")
                        else:
                            if message.content:
                                print(f"Assistant: {message.content}")
            except Exception as e:
                print(f"Error processing event: {e}")

async def main_async():
    """Main entry point for the CLI."""
    if len(sys.argv) > 1:
        try:
            claim_id = int(sys.argv[1])
            await run_workflow(claim_id)
        except ValueError:
            print("Usage: python src/main.py <claim_id>")
    else:
        # Default for testing
        await run_workflow(1)

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()

