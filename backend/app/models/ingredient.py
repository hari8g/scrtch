from pydantic import BaseModel
from typing import Dict, Any


class Ingredient(BaseModel):
    name: str
    attributes: Dict[str, Any] 