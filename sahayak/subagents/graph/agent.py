from google.adk.agents import Agent
from sahayak.tools.graph import GraphVisualizer
from sahayak.subagents.graph.prompt import GRAPH_AGENT_INSTR

# Create the agent with the proper tool instance
graph_agent = Agent(
    name="graph_visualizer",
    model="gemini-2.5-flash",
    description="Queries student performance in Neo4j.",
    tools=[GraphVisualizer()],
    instruction=GRAPH_AGENT_INSTR,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)