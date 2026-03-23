from pydantic import BaseModel
from typing import List, Dict, Optional


class StepRequest(BaseModel):
    steps: List[Dict]
    frs: Optional[str] = None