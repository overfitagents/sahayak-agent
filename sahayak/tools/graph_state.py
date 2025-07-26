from pydantic import BaseModel
from typing import Optional

class GraphQueryState(BaseModel):
    user_intent: Optional[str] = None
    topic_a: Optional[str] = None
    topic_b: Optional[str] = None
    grade: Optional[str] = None