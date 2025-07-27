import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
from sahayak import prompt
from sahayak.subagents.planner.agent import planner_agent
from sahayak.subagents.query.agent import query_agent
from sahayak.subagents.academia.agent import academia_agent
from sahayak.subagents.reminder.agent import task_agent

print(prompt.ROOT_INSTRUCTION)
root_agent = Agent(
    name="TeacherAssistant",
    model="gemini-2.5-flash",
    description=(
        "An AI assistant specialized in helping teachers with educational tasks "
        "including lesson planning, content creation, classroom management, "
        "student performance analysis, and academic insights,"
        "reminders, task management, friendly conversations, and more."
    ),
    instruction=prompt.ROOT_INSTRUCTION,
    sub_agents=[planner_agent, query_agent, academia_agent, task_agent],
    # before_agent_callback=_load_initial_state,
)

# "Help teachers create and manage educational content and tasks including: "
#     "- Designing lesson plans and curricula\n"
#     "- Generating educational materials and visual aids\n"
#     "- Creating assignments and assessments\n"
#     "- Managing class schedules and reminders\n"
#     "- Developing student progress tracking systems"
