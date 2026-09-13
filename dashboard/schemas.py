"""JSON contract for LLM insights, shared by generate_insights.py (writer) and app.py (reader)."""
from typing import Literal

from pydantic import BaseModel, Field

Urgency = Literal['red', 'yellow', 'green']
Actor = Literal['Marine park authority', 'Tourism operators']
Timeframe = Literal['Now', 'Before next bleaching season', 'Ongoing']


class Driver(BaseModel):
    factor: str = Field(description='Short name of the factor, e.g. "Heat stress" or "Anchor damage"')
    evidence: str = Field(description='The data behind it, quoting only numbers given in the input')


class Action(BaseModel):
    action: str = Field(description='A concrete, practical action')
    actor: Actor
    timeframe: Timeframe
    rationale: str = Field(description='Why this action fits this island, referring to the input data')


class IslandInsight(BaseModel):
    island: str
    urgency: Urgency
    headline: str = Field(description='One sentence, at most 20 words')
    why: str = Field(description='2-3 sentences explaining the urgency level')
    drivers: list[Driver] = Field(min_length=1, max_length=4)
    actions: list[Action] = Field(min_length=2, max_length=4)
    monitoring: str = Field(description='What to check at the next survey')
    confidence: Literal['low', 'medium', 'high']
    caveats: str = Field(description='Limits of the evidence for this island')


class IslandInsights(BaseModel):
    """Batch response: one insight per island in the request."""
    insights: list[IslandInsight] = Field(min_length=1)


class PriorityIsland(BaseModel):
    island: str
    reason: str


class RegionalPattern(BaseModel):
    region: str
    pattern: str


class Overview(BaseModel):
    headline: str = Field(description='One sentence, at most 25 words')
    key_findings: list[str] = Field(min_length=3, max_length=5)
    top_priority_islands: list[PriorityIsland] = Field(min_length=1, max_length=6)
    regional_patterns: list[RegionalPattern] = Field(min_length=1, max_length=4)
    heat_outlook_2026: str
    caveats: str
