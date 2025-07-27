"""
Task and Reminder Agent for the Sahayak educational assistant.

This agent handles scheduling, timetables, reminders, and friendly task management conversations.
It provides a supportive interface for teachers to manage their daily tasks and schedules.
"""

from google.adk.agents import Agent
from sahayak.tools.reminder import create_reminder
from sahayak.tools.memory import memorize, memorize_list
from sahayak.subagents.reminder import prompt

# Create the task and reminder agent
task_agent = Agent(
    name="task_agent",
    model="gemini-2.5-pro",
    description=(
        "A friendly task and reminder assistant that helps teachers manage schedules, "
        "timetables, reminders, and daily tasks. Provides timetable information, "
        "creates smart reminders, and offers supportive conversation about task management."
    ),
    tools=[
        create_reminder
    ],
    instruction=prompt.TASK_AGENT_INSTRUCTION,
)
