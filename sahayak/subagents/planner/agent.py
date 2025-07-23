"""
PlannerBot is a sub-agent of the TeacherAssistant agent. It specializes in curriculum planning, lesson design, and content creation.
"""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from sahayak.tools.rag import ask_vertex_retrieval, rag_query
from sahayak.subagents.planner import prompt
from sahayak.tools.memory import memorize, memorize_list, memorize_dict, load_recent_curriculum, load_recent_lesson_plan, load_recent_whiteboard


curriculum_planner = Agent(
    name="curriculum_planner",
    model="gemini-2.5-flash",
    description=(
        "An AI assistant specialized in yearly curriculum planning, calendar integration, "
        "and resource allocation based on local context."
    ),
    tools=[rag_query],
    instruction=prompt.CURRICULUM_PLANNER_INSTR,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

lesson_designer = Agent(
    name="lesson_designer",
    model="gemini-2.5-flash",
    description=(
        "An AI assistant specialized in creating detailed lesson plans, interactive slides, "
        "and teaching aids."
    ),
    tools=[ask_vertex_retrieval],
    instruction=prompt.LESSON_DESIGNER_INSTR,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

content_creator = Agent(
    name="content_creator",
    model="gemini-2.5-flash",
    description=(
        "An AI assistant specialized in producing educational materials, managing presentation "
        "flows, and creating assessments."
    ),
    tools=[ask_vertex_retrieval],
    instruction=prompt.CONTENT_CREATOR_INSTR,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

planner_agent = Agent(
    name="planner_agent",
    model="gemini-2.5-flash",
    description=(
        "An AI assistant specialized in curriculum planning, lesson design, and content creation. "
        "Coordinates between curriculum planning, lesson design, and content creation sub-agents."
    ),
    sub_agents=[curriculum_planner, lesson_designer, content_creator],
    tools=[
        memorize_dict,
        load_recent_curriculum,
        load_recent_lesson_plan,
        load_recent_whiteboard,
    ],
    instruction=prompt.PLANNER_INSTR,
)
