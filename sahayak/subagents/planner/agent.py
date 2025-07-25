"""
PlannerBot is a sub-agent of the TeacherAssistant agent. It specializes in curriculum planning, lesson design, and content creation.
"""

from google.adk.agents import Agent, LlmAgent
from google.adk.tools.agent_tool import AgentTool
from sahayak.tools.rag import ask_vertex_retrieval, rag_query
from sahayak.tools.image import create_slide_images
from sahayak.subagents.planner import prompt
from sahayak.tools.memory import memorize, memorize_list, memorize_dict, load_recent_curriculum, load_recent_lesson_plan, load_recent_whiteboard
from sahayak.shared_libs import types

curriculum_planner = Agent(
    name="curriculum_planner",
    model="gemini-2.5-flash",
    description=(
        "An AI assistant specialized in yearly curriculum planning, calendar integration, "
        "and resource allocation based on local context."
    ),
    tools=[rag_query, memorize],
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
    tools=[rag_query, memorize],
    instruction=prompt.LESSON_DESIGNER_INSTR,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)


interactive_whiteboard = Agent(
    name="interactive_whiteboard",
    model="gemini-2.5-flash",
    description=(
        "An AI assistant specialized in creating interactive whiteboard content/diagrams/flowcharts (image) based on the requested topic."
    ),
    tools=[rag_query, memorize, memorize_dict],
    # instruction=prompt.INTERACTIVE_WHITEBOARD_INSTR,
    instruction=(
        "You are an interactive whiteboard expert who creates diagrams, flowcharts, and visual aids based on the requested topic."
    ),
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

questions_generator = Agent(
    name="questions_generator",
    model="gemini-2.5-flash",
    description=(
        "An AI assistant specialized in generating questions and quizzes based on the requested topic and lesson plan."
    ),
    tools=[rag_query, memorize, memorize_dict],
    # instruction=prompt.QUESTIONS_GENERATOR_INSTR,
    instruction=(
        "You are a questions generator expert who creates quizzes and questions based on the requested topic and lesson plan."
    ),
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

# this agent is like, for questions like can you explain me this topic in detail, you provide an analogy based example based on the hyper localized content, or an example that could relate to the students easily or can teachers themselves understand kind of, it also handles queries like what topics should i cover today
topic_helper = Agent(
    name="topic_helper",
    model="gemini-2.5-flash",
    description=(
        "An AI assistant specialized in explaining topics through relatable analogies and examples"
        "based on localized context to help both students and teachers understand concepts better."
    ),
    tools=[rag_query, memorize, memorize_dict],
    # instruction=prompt.TOPIC_HELPER_INSTR,
    instruction=(
        "You are a topic helper expert who explains topics through relatable analogies and examples based on localized context."
    ),
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

generate_slide_contents = LlmAgent(
    name="generate_slide_contents",
    model="gemini-2.5-flash",
    description=(
        "An AI agent specialized in generating slide contents based on the requested topics and lesson plan."
    ),
    instruction=prompt.GENERATE_SLIDE_CONTENTS_INSTR,
    output_key="slide_contents",
    output_schema=types.SlideContents,
)

presentation_generator = Agent(
    name="presentation_generator",
    model="gemini-2.5-flash",
    description=(
        "An AI assistant specialized in generating interactive presentation slides with visual aids based on the requested topic and lesson plan."
    ),
    tools=[
        AgentTool(generate_slide_contents),
        rag_query,
        memorize,
        memorize_dict,
        create_slide_images,
    ],
    instruction=prompt.PRESENTATION_GENERATOR_INSTR,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)


content_creator = Agent(
    name="content_creator",
    model="gemini-2.5-flash",
    description=(
        "An AI assistant specialized in producing educational materials, managing presentation flows, creating assessments, or helping teachers with topics to be covered based on the curriculum and lesson plans."
    ),
    sub_agents=[
        presentation_generator,
        interactive_whiteboard,
        questions_generator,
        topic_helper,
    ],
    tools=[rag_query],
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
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
