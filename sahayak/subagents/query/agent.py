"""
Query Agent System - Main module for handling teacher queries related to teaching content.
This system includes specialized sub-agents for different types of queries:
1. Textbook Content Queries (using RAG)
2. Interactive Image Analysis (RAG + Image Fetching + Marked Section Analysis)
3. Flow Diagram Queries (Flow diagram generation)
"""

from google.adk.agents import Agent, LlmAgent
from google.adk.tools.agent_tool import AgentTool
from sahayak.tools.rag import ask_vertex_retrieval, rag_query
from sahayak.tools.image import fetch_textbook_image
from sahayak.subagents.planner import prompt
from sahayak.tools.memory import (
    memorize,
    memorize_list,
    memorize_dict,
    load_recent_curriculum,
    load_recent_lesson_plan,
    load_recent_whiteboard,
)
from sahayak.shared_libs import types
from google.adk.tools import google_search

# Sub-agent for handling textbook content queries with analogies and examples
textbook_content_agent = Agent(
    name="textbook_content_agent",
    model="gemini-2.5-pro",
    description=(
        "An AI assistant specialized in answering textbook-related questions using RAG retrieval "
        "and generating relatable analogies and examples to help teachers explain concepts better."
    ),
    tools=[rag_query, memorize, memorize_dict],
    instruction=(
        "You are a textbook content expert who answers questions about textbook material. "
        "First check if `current_grade`: {current_grade} has been set.\n If not, check with the user for the grade it's looking for.\n Once you know, use `memorize_dict` to store the current grade and then proceed with their query.\n"
        "For each query:\n"
        "1. Use `rag_query` to retrieve relevant content from the textbook\n"
        "2. Provide comprehensive answers based on the retrieved content\n"
        "3. Generate relatable analogies and real-world examples to help teachers explain concepts\n"
        "4. Focus on making complex topics easy to understand and teach\n"
        "5. Always cite the source material when providing answers\n"
        "6. If additional context is needed, suggest follow-up questions or related topics"
        "7. Ensure the response is pedagogically sound and suitable for classroom use"
        "8. Do not generate long text heavy content, keep it concise and focused"
        "9. If the query isn't clear, or needs more context, ask clarifying questions to better understand the teacher's needs"
    ),
    # disallow_transfer_to_parent=True,
    # disallow_transfer_to_peers=True,
)

# Sub-agent for handling interactive image queries and analysis
interactive_image_agent = Agent(
    name="interactive_image_agent",
    model="gemini-2.5-pro",
    description=(
        "An AI assistant specialized in fetching textbook images and providing interactive analysis"
        "based on specific parts marked by teachers for clarification, analogies, and educational activities."
    ),
    tools=[fetch_textbook_image],
    instruction=(
        "You are an interactive image analysis expert who helps teachers with textbook images. "
        "For each image-related request:\n"
        "1. FETCH the requested image from the textbook using the tool `fetch_textbook_image`\n"
        "2. Analyse the tool response, and if it has a `message` directly send that as reply, DO NOT REFERENCE THE IMAGE LINK.\n"
        "3. ANALYZE marked or circled parts of images when teachers highlight specific areas\n"
        "4. For marked image sections, provide:\n"
        "   - Detailed explanations of the highlighted components\n"
        "   - Relatable analogies to help explain complex parts\n"
        "   - In-depth analysis of the marked areas\n"
        "   - Educational context and significance\n"
        "   - Clarifying questions about marked sections\n"
        "   - Sample activities related to the image components\n"
        "   - Quiz questions focusing on highlighted areas\n"
        "   - Discussion prompts for classroom use\n"
        " etc, based on the requested image and teacher's needs\n"
        "5. Always reference the specific marked areas and provide targeted explanations"
    ),
    # disallow_transfer_to_parent=True,
    # disallow_transfer_to_peers=True,
)

# Sub-agent for generating flow diagrams
flow_diagram_agent = Agent(
    name="flow_diagram_agent",
    model="gemini-2.5-flash",
    description=(
        "An AI assistant specialized in creating flow diagrams, process charts, and visual "
        "representations of concepts, processes, or systems based on textbook content."
    ),
    tools=[rag_query, memorize, memorize_dict],
    instruction=(
        "You are a flow diagram specialist who creates visual process representations. "
        "For each flow diagram request:\n"
        "1. Use RAG tools to gather relevant information about the process or concept\n"
        "2. Break down complex processes into clear, logical steps\n"
        "3. Create comprehensive flow diagrams that include:\n"
        "   - Clear start and end points\n"
        "   - Logical flow with decision points where applicable\n"
        "   - Descriptive labels and annotations\n"
        "   - Visual elements that enhance understanding\n"
        "4. Generate image descriptions for flowcharts that are:\n"
        "   - Easy to follow and understand\n"
        "   - Pedagogically sound for teaching purposes\n"
        "   - Visually appealing and engaging\n"
        "5. Provide explanations for each step in the flow diagram"
    ),
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

# Main query agent that routes queries to appropriate sub-agents
query_agent = Agent(
    name="query_agent",
    model="gemini-2.5-flash",
    description=(
        "Main query handling agent for teacher questions related to teaching content. "
        "Routes queries to specialized sub-agents based on the type of request: "
        "textbook content, interactive image analysis, or flow diagrams."
    ),
    sub_agents=[textbook_content_agent, interactive_image_agent, flow_diagram_agent],
    tools=[memorize],
    instruction=(
        "You are the main query routing agent for teacher assistance. Your role is to:\n\n"
        "1. ANALYZE the incoming teacher query to determine its type:\n"
        "   - Textbook content questions (facts, explanations, analogies needed)\n"
        "   - Interactive image requests (fetch images and analyze marked sections)\n"
        "   - Flow diagram requests (process visualization, concept mapping)\n\n"
        "2. ROUTE the query to the appropriate sub-agent:\n"
        "   - Use 'textbook_content_agent' for general textbook questions, concept explanations, and analogy requests\n"
        "   - Use 'interactive_image_agent' for fetching textbook images and analyzing marked/highlighted sections\n"
        "   - Use 'flow_diagram_agent' for creating process flows, concept maps, or visual representations\n\n"
        "3. COORDINATE with sub-agents to ensure comprehensive responses\n\n"
        "4. SYNTHESIZE results if multiple sub-agents are needed for a complex query\n\n"
        "Always prioritize educational value and teaching effectiveness in your responses."
    ),
    # disallow_transfer_to_parent=False,
    # disallow_transfer_to_peers=True,
)
