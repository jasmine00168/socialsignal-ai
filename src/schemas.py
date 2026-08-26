from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DemandAnalysis(BaseModel):
    """Stable data contract for one social post analysis."""

    model_config = ConfigDict(extra="forbid")

    is_demand: bool = Field(description="Whether the post expresses a software-related need.")
    demand_type: Literal[
        "efficiency",
        "information",
        "creation",
        "commerce",
        "management",
        "communication",
        "other",
        "none",
    ]
    opportunity_title: str = Field(description="Short, neutral opportunity name in Chinese.")
    target_user: str = Field(description="Who experiences the problem; unknown if absent.")
    usage_context: str = Field(description="When or where the problem happens.")
    pain_point: str = Field(description="The concrete problem without inventing facts.")
    desired_solution: str = Field(description="The desired outcome or software capability.")
    existing_workaround: str | None = Field(description="Current workaround if explicitly stated.")
    willingness_to_pay: Literal["unknown", "low", "medium", "high"]
    urgency: int = Field(ge=1, le=5)
    confidence: float = Field(ge=0, le=1)
    evidence_quote: str = Field(description="A short verbatim quote copied from the source post.")
    reasoning_summary: str = Field(description="One-sentence explanation in Chinese.")


class DemandAnalysisResult(DemandAnalysis):
    """Application result enriched with provenance and validation."""

    post_id: str
    evidence_verified: bool
    model: str


class ClusterAssignment(BaseModel):
    """One demand-to-cluster assignment produced by the model."""

    model_config = ConfigDict(extra="forbid")

    post_id: str
    cluster_id: str = Field(description="Stable short identifier such as cluster-01.")
    cluster_label: str = Field(description="Concise Chinese label describing the shared need.")


class DemandClusters(BaseModel):
    """Structured contract for a complete set of cluster assignments."""

    model_config = ConfigDict(extra="forbid")

    assignments: list[ClusterAssignment]
