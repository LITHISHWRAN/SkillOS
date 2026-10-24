from pydantic import BaseModel, Field

class SkillTextRequest(BaseModel):
    content: str = Field(min_length=1, max_length=50000)
    directory_name: str | None = None

class GenerateRequest(BaseModel):
    task: str = Field(min_length=3, max_length=2000)
    model_instructions: str | None = Field(default=None, max_length=2000)

class ImproveRequest(BaseModel):
    content: str = Field(min_length=1, max_length=50000)
    findings: list[str] = Field(default_factory=list, max_length=30)
    intended_behavior: str | None = Field(default=None, max_length=2000)
