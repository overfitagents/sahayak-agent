# Create the Academic Performance Analysis Agent
from google.adk.agents import Agent
from sahayak.tools.graph import GraphVisualizer
from sahayak.subagents.academia.prompt import ACADEMIA_AGENT_INSTR, STUDENT_PERFORMANCE_ANALYZER_INSTR

# Student Performance Analyzer sub-agent (renamed from graph_visualizer for clarity)
student_performance_analyzer = Agent(
    name="student_performance_analyzer",
    model="gemini-2.5-flash",
    description="Analyzes student performance data from Neo4j database, creates study teams, and generates academic statistics.",
    tools=[GraphVisualizer()],
    instruction=STUDENT_PERFORMANCE_ANALYZER_INSTR,
    # Allow parent communication for coordinated analysis
    # disallow_transfer_to_parent=True,
    # disallow_transfer_to_peers=True,
)

# Main Academia Agent
academia_agent = Agent(
    name="academia_agent",
    model="gemini-2.5-flash",
    description="Comprehensive academic performance analysis agent that provides insights on student performance, creates study teams, generates educational statistics, and offers data-driven learning recommendations.",
    instruction=ACADEMIA_AGENT_INSTR,
    sub_agents=[student_performance_analyzer],
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)