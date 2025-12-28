from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AttributeType(str, Enum):
    occurrence = "occurrence"
    completeness = "completeness"
    accuracy = "accuracy"
    timeliness = "timeliness"
    authorization = "authorization"
    sod = "sod"


class ControlCreate(BaseModel):
    name: str
    description: str
    attributes: List[AttributeType]
    owner: Optional[str] = None


class Control(BaseModel):
    id: str
    name: str
    description: str
    attributes: List[AttributeType]
    owner: Optional[str] = None
    created_at: datetime


class EvidenceMetadata(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime
    linked_control_id: Optional[str] = None
    notes: Optional[str] = None
    sha256: str
    storage_path: Optional[str] = None
    extracted_fields: Dict[str, str] = Field(default_factory=dict)
    extraction_status: str = "pending"
    potential_exceptions: List[str] = Field(default_factory=list)
    authenticity_score: Optional[float] = None
    authenticity_notes: Optional[str] = None


class TestRunRequest(BaseModel):
    control_id: str
    evidence_ids: List[str]


class TestFinding(BaseModel):
    attribute: AttributeType
    result: str
    explanation: str
    evidence_ids: List[str] = Field(default_factory=list)


class TestRunResult(BaseModel):
    id: str
    control_id: str
    findings: List[TestFinding]
    exceptions: List[str]
    created_at: datetime


class Workpaper(BaseModel):
    id: str
    test_run_id: str
    summary: str
    conclusion: str
    created_at: datetime
