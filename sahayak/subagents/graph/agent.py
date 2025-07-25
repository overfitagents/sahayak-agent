# sahayak/subagents/graph/agent.py
from google.adk.agents import Agent
from sahayak.tools.graph import query_graph
import re

GRAPH_AGENT_INSTR = """
You are GraphVisualizer, an educational data analyst that helps teachers understand student performance by querying a Neo4j knowledge graph.

When users ask about student performance, follow these steps:

1. **Extract the request details:**
   - Intent: "find_highest" (for highest scorer) or "form_teams" (for study groups)
   - Topic(s): the subject area(s) mentioned
   - Grade: the grade level (if specified)

2. **Set these parameters in your tool context state** before calling query_graph:
   - user_intent: "find_highest" or "form_teams"
   - topic_a: first topic name
   - topic_b: second topic name (for team formation)
   - grade: grade level (if mentioned)

3. **Call query_graph()** - it will automatically read parameters from your state

4. **Explain the results** in teacher-friendly terms

Examples:
- User: "Who scored highest in light for grade 10?"
  Your response should find and explain the top performer
  
- User: "Form study teams in grade 8 for motion and forces"  
  Your response should suggest complementary pairs

Focus on providing actionable insights for teaching.
"""

def extract_study_query_params(user_query: str):
    """Extract intent, topics, and grade from user query"""
    user_query = user_query.lower().strip()
    result = {
        "user_intent": None,
        "topic_a": None,
        "topic_b": None,
        "grade": None,
    }

    # Detect intent
    if any(keyword in user_query for keyword in ["study team", "form", "group", "pair"]):
        result["user_intent"] = "form_teams"
    elif any(keyword in user_query for keyword in ["highest", "top", "scored the highest", "who scored"]):
        result["user_intent"] = "find_highest"

    # Detect grade
    grade_match = re.search(r"(?:grade|class)\s*(\d+)", user_query)
    if grade_match:
        result["grade"] = grade_match.group(1)

    # Extract topics - try multiple patterns
    patterns = [
        r"(?:topic\s+|in\s+(?:the\s+)?)([a-zA-Z]+)(?:\s+and\s+([a-zA-Z]+))?",
        r"([a-zA-Z]+)\s+and\s+([a-zA-Z]+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, user_query)
        if match:
            result["topic_a"] = match.group(1)
            if len(match.groups()) > 1 and match.group(2):
                result["topic_b"] = match.group(2)
            break
    
    # Fallback for single topic
    if not result["topic_a"]:
        simple_match = re.search(r"(?:in|for|topic)\s+([a-zA-Z]+)", user_query)
        if simple_match:
            result["topic_a"] = simple_match.group(1)

    return result

# Create the agent
graph_visualizer = Agent(
    name="graph_visualizer",
    model="gemini-2.5-flash",
    description="Analyzes student performance data using Neo4j graph queries.",
    tools=[query_graph],
    instruction=GRAPH_AGENT_INSTR,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)