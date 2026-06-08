from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime

class SimulationStartRequest(BaseModel):
    url: str = Field(..., description="Target website URL to simulate user behavior on")
    num_personas: int = Field(default=3, ge=1, le=10, description="Number of personas to generate (max 10)")
    use_shared_session: bool = Field(default=False, description="Whether to load the shared login session state")

class PersonaSchema(BaseModel):
    id: str
    simulation_id: str
    name: str
    archetype: str
    goals: List[str]
    impatience: float = Field(..., ge=0.0, le=1.0)
    tech_savviness: float = Field(..., ge=0.0, le=1.0)
    price_sensitivity: float = Field(..., ge=0.0, le=1.0)
    support_reliance: float = Field(..., ge=0.0, le=1.0)
    status: str  # pending, running, completed, churned, failed

class AgentLogSchema(BaseModel):
    id: Optional[int] = None
    simulation_id: str
    persona_id: str
    timestamp: datetime
    step_number: int
    action: str  # Click, Type, Wait, Back, Complete, Churn
    url: str
    description: str
    screenshot_filename: Optional[str] = None
    reason: Optional[str] = None

class BugSchema(BaseModel):
    severity: str  # Critical, Major, Minor
    description: str
    selector: Optional[str] = None
    url: Optional[str] = None
    screenshot: Optional[str] = None

class ReportResponse(BaseModel):
    id: str
    simulation_id: str
    nps: int
    churn_rate: float
    wtp: str
    bugs: List[BugSchema]
    summary: str  # Markdown text
    created_at: datetime

class SimulationStatusResponse(BaseModel):
    id: str
    url: str
    status: str  # pending, running, completed, failed
    created_at: datetime
    nps: Optional[int] = None
    churn_rate: Optional[float] = None
    wtp: Optional[str] = None
    personas: List[PersonaSchema] = []
    use_shared_session: bool = False

class ChatMessageSchema(BaseModel):
    id: Optional[int] = None
    simulation_id: str
    role: str  # user, assistant
    content: str
    timestamp: datetime

class ChatRequest(BaseModel):
    message: str
