from google.adk.agents import Agent
from sahayak.tools.graph import query_graph
from sahayak.subagents.graph import prompt
import re

GRAPH_AGENT_INSTR = """
You are GraphVisualizer, an educational data analyst that helps teachers understand student performance.

When users ask about student performance:
1. First understand what they want (highest scorer or study teams)
2. Extract the topic(s) and grade
3. Set these parameters in your state
4. Call the query_graph tool
5. Explain the results clearly

Examples of user requests:
- "Who scored highest in light?" → find highest scorer in light topic
- "Form study teams for grade 8 in motion and forces" → form complementary teams

Always be helpful and explain what the data means for teaching.
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

    # Extract topics
    topic_patterns = [
        r"(?:topic\s+|in\s+(?:the\s+)?)([a-zA-Z]+)(?:\s+and\s+([a-zA-Z]+))?",  
        r"([a-zA-Z]+)\s+and\s+([a-zA-Z]+)"  
    ]
    
    for pattern in topic_patterns:
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

# The agent needs to use a custom handler to set state before calling tool
# But since you're using Google ADK, let's make sure the instruction is clear:

GRAPH_AGENT_INSTR = """
You are GraphVisualizer, an educational data analyst. When users ask about student performance:

1. First identify their intent (finding highest scorer or forming teams)
2. Extract the topic(s) and grade level from their request
3. **IMPORTANT**: Before calling query_graph, you MUST set these parameters in your state:
   - user_intent: "find_highest" or "form_teams"  
   - topic_a: the main topic (required)
   - topic_b: second topic (for team formation)
   - grade: grade level (if mentioned)
4. Then call query_graph() with no parameters
5. Format the results clearly

Example workflow:
User: "Who scored highest in light for grade 10?"
You should set state: {user_intent: "find_highest", topic_a: "light", grade: "10"}
Then call: query_graph()

The tool will read these parameters from your state automatically.
"""

graph_visualizer = Agent(
    name="graph_visualizer",
    model="gemini-2.5-flash",
    description="Analyzes student performance data using Neo4j graph queries.",
    tools=[query_graph],
    instruction=GRAPH_AGENT_INSTR,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)