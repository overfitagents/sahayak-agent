import asyncio
import os
import json
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents import Agent
from sahayak.subagents.graph.agent import graph_agent
from sahayak.tools.graph import GraphVisualizer
from google.genai import types

# Load environment variables
load_dotenv()

async def execute_tool_manually(tool_call):
    """Execute tool call manually in async context."""
    if tool_call.get("name") == "graph_visualizer":
        print("🔧 Manually executing GraphVisualizer (async)...")
        tool = GraphVisualizer()
        
        # Get the arguments
        args = tool_call["arguments"]
        
        # Build state dict
        state = {
            "user_intent": args.get("user_intent"),
            "topic_a": args.get("topic_a"),
            "grade": args.get("grade"),
            "topic_b": args.get("topic_b")
        }
        
        # Validate state
        try:
            from sahayak.tools.graph_state import GraphQueryState
            parsed_state = GraphQueryState(**{k: v for k, v in state.items() if v is not None})
        except Exception as e:
            return f"Invalid parameters: {e}"
        
        # Execute the async query
        try:
            result = await tool._run_query(parsed_state)
            return result
        except Exception as e:
            return f"Query failed: {e}"

async def main():
    app_name = "sahayak_agent_app"
    user_id = "test_user"
    session_id = "test_session"

    session_service = InMemorySessionService()

    session = await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id
    )

    runner = Runner(
        agent=graph_agent,
        app_name=app_name,
        session_service=session_service
    )

    query = "Form teams based on performance in topics 'light' and 'plants' for grade 6"
    content = types.Content(role="user", parts=[types.Part(text=query)])

    events = runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message=content
    )

    print("=== ALL EVENTS ===")
    final_response_text = ""
    
    for i, event in enumerate(events):
        print(f"\n--- Event #{i} ---")
        print(f"Type: {type(event)}")
        
        if hasattr(event, 'is_final_response') and event.is_final_response():
            print(">>> This is a FINAL RESPONSE")
            if hasattr(event, 'content') and event.content is not None:
                print(f"Content: {event.content}")
                if hasattr(event.content, 'parts') and event.content.parts:
                    raw_text = event.content.parts[0].text
                    print(f"[Raw Text]: {raw_text}")
                    
                    # Try to parse as tool call
                    try:
                        # Remove markdown if present
                        if "```json" in raw_text:
                            json_str = raw_text.split("```json")[1].split("```")[0]
                        else:
                            json_str = raw_text
                            
                        tool_call = json.loads(json_str)
                        print(f"[Parsed Tool Call]: {tool_call}")
                        
                        # If it's our tool, execute it manually (async)
                        if tool_call.get("name") == "graph_visualizer":
                            result = await execute_tool_manually(tool_call)
                            final_response_text = result
                            print(f"[Tool Result]: {final_response_text}")
                            break
                            
                    except Exception as e:
                        print(f"❌ Failed to parse tool call: {e}")
                        final_response_text = raw_text
                        break

    print("\n=== SUMMARY ===")
    if final_response_text:
        print("Final Response:")
        print(final_response_text)
    else:
        print("No final response was generated.")

if __name__ == "__main__":
    asyncio.run(main())