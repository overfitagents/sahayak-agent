from datetime import datetime
import json
import os
from typing import Dict, Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.sessions.state import State
from google.adk.tools import ToolContext

# from src.shared_libraries import constants


def memorize_list(key: str, value: list, tool_context: ToolContext):
    """
    Memorize pieces of information as a list.

    Args:
        key: the label indexing the memory to store the value.
        value: the list of information to be stored.
        tool_context: The ADK tool context.

    Returns:
        A status message.
    """
    mem_dict = tool_context.state

    mem_dict[key] = value

    print({"status": f'Stored "{key}": {mem_dict[key]}', "mem_dict": mem_dict})
    return {"status": f'Stored "{key}": {mem_dict[key]}'}


def memorize(key: str, value: str, tool_context: ToolContext):
    """
    Memorize pieces of information, one key-value pair at a time.

    Args:
        key: the label indexing the memory to store the value.
        value: the information to be stored.
        tool_context: The ADK tool context.

    Returns:
        A status message.
    """
    print(f"Memorizing {key}: {value}")
    mem_dict = tool_context.state
    if value.startswith("```json") and value.endswith("```"):
        # Extract JSON content between backticks and parse it
        json_str = value[7:-3].strip()  # Remove ```json and ``` markers
        try:
            mem_dict[key] = json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {str(e)}")
            mem_dict[key] = value
    else:
        mem_dict[key] = value
    return {"status": f'Stored "{key}": {mem_dict[key]}'}


def memorize_dict(key: str, value: dict, tool_context: ToolContext):
    """
    Memorize pieces of information, one key-value pair at a time.

    Args:
        key: the label indexing the memory to store the value.
        value: the information to be stored.
        tool_context: The ADK tool context.

    Returns:
        A status message.
    """
    mem_dict = tool_context.state
    if key == "current_pets":
        mem_dict[key] = [value]

    else:
        mem_dict[key] = value
    return {"status": f'Stored "{key}": "{value}"'}


def forget(key: str, value: str, tool_context: ToolContext):
    """
    Forget pieces of information.

    Args:
        key: the label indexing the memory to store the value.
        value: the information to be removed.
        tool_context: The ADK tool context.

    Returns:
        A status message.
    """
    if tool_context.state[key] is None:
        tool_context.state[key] = []
    if value in tool_context.state[key]:
        tool_context.state[key].remove(value)
    return {"status": f'Removed "{key}": "{value}"'}

def load_recent_curriculum(current_grade: int, tool_context: ToolContext):
    """
    Load the most recent curriculum for a specific grade level.

    Args:
        tool_context: The ADK tool context.
        current_grade: The current grade level.

    Returns:
        The loaded curriculum as a dictionary.
    """

    mem_dict = tool_context.state
    if mem_dict.get("curriculum") is {}:
        mem_dict["curriculum"] = {}
    return {"status": f'Stored "curriculum": "{mem_dict["curriculum"]}"'}

def load_recent_lesson_plan(current_grade: int, tool_context: ToolContext):
    """
    Load the most recent lesson plan for a specific grade level.

    Args:
        tool_context: The ADK tool context.
        current_grade: The current grade level.

    Returns:
        The loaded lesson plan as a dictionary.
    """

    mem_dict = tool_context.state
    mem_dict["current_lesson_plan"] = {}
    return {"status": f'Stored "current_lesson_plan": "{mem_dict["current_lesson_plan"]}"'}

def load_recent_whiteboard(current_grade: int, tool_context: ToolContext):
    """
    Load the most recent whiteboard content for a specific grade level.

    Args:
        tool_context: The ADK tool context.
        current_grade: The current grade level.

    Returns:
        The loaded whiteboard content as a dictionary.
    """

    mem_dict = tool_context.state
    mem_dict["current_whiteboard"] = {}
    return {"status": f'Stored "current_whiteboard": "{mem_dict["current_whiteboard"]}"'}

def _load_initial_state(callback_context: CallbackContext):
    """
    Load the initial state for the agent from a JSON file.

    Args:
        context: The callback context containing the state.

    Returns:
        The loaded state as a dictionary.
    """
    state_file = os.getenv("INITIAL_STATE_FILE", "initial_state.json")
    if not os.path.exists(state_file):
        raise FileNotFoundError(f"State file {state_file} does not exist.")

    with open(state_file, "r") as f:
        initial_state = json.load(f)

    callback_context.state.update(initial_state)
    print(f"Initial state loaded: {callback_context.state}")
    return callback_context.state
