from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class AgentAction(BaseModel):
    action_id: int

    agent_name: str

    action_type: str

    procurement_request_id: int

    description: str

    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None

    status: str = "completed"

    created_at: datetime