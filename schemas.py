from typing import List, Literal
from pydantic import BaseModel, Field

# ==========================================
# 1. NODE SCHEMAS (Entities)
# ==========================================

class Company(BaseModel):
    id: str = Field(..., description="Unique identifier, usually the company name or ticker capitalized (e.g., 'APPLE_INC')")
    name: str = Field(..., description="Full legal name of the company")
    ticker: str = Field(..., description="Stock ticker symbol, or 'PRIVATE' if not publicly traded")
    sector: str = Field(..., description="General industry sector (e.g., Technology, Healthcare, Energy)")

class Competitor(BaseModel):
    id: str = Field(..., description="Unique identifier, usually the competitor name capitalized")
    name: str = Field(..., description="Name of the competitor company or entity")

class RiskFactor(BaseModel):
    id: str = Field(..., description="A unique slug or short hash representing the risk (e.g., 'CHIP_SHORTAGE_2026')")
    description: str = Field(..., description="Detailed description of the risk factor extracted from the text")
    severity: Literal["Low", "Medium", "High", "Critical"] = Field(..., description="Assessed severity level based on text context")
    category: Literal["Supply Chain", "Regulatory", "Financial", "Cybersecurity", "Macroeconomic", "Operational"] = Field(
        ..., description="The primary classification of the risk"
    )

# ==========================================
# 2. EDGE SCHEMA (Relationships)
# ==========================================

class Relationship(BaseModel):
    source: str = Field(..., description="The 'id' of the source node")
    target: str = Field(..., description="The 'id' of the target node")
    type: Literal["COMPETES_WITH", "VULNERABLE_TO", "PARTNERS_WITH", "AFFECTS"] = Field(
        ..., description="The directional graph relationship type"
    )

# ==========================================
# 3. ROOT CONTAINER (For Gemini API response_schema)
# ==========================================

class KnowledgeGraphExtraction(BaseModel):
    """The root container that forces the LLM to return a perfectly structured graph."""
    companies: List[Company] = Field(default_factory=list, description="List of companies identified")
    competitors: List[Competitor] = Field(default_factory=list, description="List of competitors identified")
    risk_factors: List[RiskFactor] = Field(default_factory=list, description="List of risk factors identified")
    relationships: List[Relationship] = Field(
        default_factory=list, 
        description="List of directed relationships connecting the extracted nodes. Ensure source and target IDs match exactly."
    )
