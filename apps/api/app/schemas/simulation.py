from pydantic import BaseModel, Field


class SimulationAnswerRequest(BaseModel):
    selected_option: int = Field(ge=0, le=10)

