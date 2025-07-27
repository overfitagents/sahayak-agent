"""
Reminder and scheduling tools for the Task Agent.
"""

from datetime import datetime, timedelta
from typing import Any, Dict
import json
import re

from google.adk.tools import ToolContext


def create_reminder(title: str, description: str, datetime_to_send: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Create a reminder to be sent at a specified time.
    
    Args:
        title: The title/subject of the reminder
        description: Detailed description of what to remind about
        datetime_to_send: When to send the reminder (ISO format: YYYY-MM-DD HH:MM:SS or relative like "in 5 minutes")
        
    Returns:
        A dictionary with the reminder creation status and details
    """
    
    return {
        "status": "success",
        "title": title,
        "description": description,
        "scheduled_time": datetime_to_send
    }
