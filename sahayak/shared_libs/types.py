from pydantic import BaseModel
from typing import List

class Slide(BaseModel):
    heading: str
    points: List[str]
    image_description: str


class SlideContents(BaseModel):
    slides: List[Slide]
