from datetime import datetime
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    Control,
    ControlCreate,
    EvidenceMetadata,
    AttributeType,
    TestFinding,
    TestRunRequest,
    TestRunResult,
    Workpaper,
)

app = FastAPI(title="AuditPilot-SOX MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
EVIDENCE_DIR = BASE_DIR / "evidence"
EVIDENCE_DIR.mkdir(exist_ok=True)
MAX_UPLOAD_BYTES = 50 * 1024 * 1024

CONTROLS: Dict[str, Control] = {}
EVIDENCE: Dict[str, EvidenceMetadata] = {}
TEST_RUNS: Dict[str, TestRunResult] = {}
WORKPAPERS: Dict[str, Workpaper] = {}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/controls", response_model=Control)
def create_control(payload: ControlCreate) -> Control:
    control_id = str(uuid4())
    control = Control(
        id=control_id,
        name=payload.name,
        description=payload.description,
        attributes=payload.attributes,
        owner=payload.owner,
        created_at=datetime.utcnow(),
    )
    CONTROLS[control_id] = control
    return control


@app.get("/controls", response_model=List[Control])
def list_controls() -> List[Control]:
    return list(CONTROLS.values())


def _extract_fields(filename: str, content: bytes) -> Dict[str, str]:
    text = ""
    if filename.lower().endswith((".txt", ".csv")):
        text = content.decode("utf-8", errors="ignore")

    fields: Dict[str, str] = {}
    if text:
        date_match = re.search(r"(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})", text)
        amount_match = re.search(r"\$?\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?", text)
        preparer_match = re.search(r"(preparer|prepared by)[:\s]+([A-Za-z ,.'-]+)", text, re.IGNORECASE)
        approver_match = re.search(r"(approver|approved by)[:\s]+([A-Za-z ,.'-]+)", text, re.IGNORECASE)

        if date_match:
            fields["date"] = date_match.group(0)
        if amount_match:
            fields["amount"] = amount_match.group(0).strip()
        if preparer_match:
            fields["preparer"] = preparer_match.group(2).strip()
        if approver_match:
            fields["approver"] = approver_match.group(2).strip()
    return fields


def _cross_validate(control: Control, fields: Dict[str, str]) -> List[str]:
    exceptions: List[str] = []
    if AttributeType.authorization in control.attributes and "approver" not in fields:
        exceptions.append("Missing approver for authorization attribute.")
    if AttributeType.timeliness in control.attributes and "date" not in fields:
        exceptions.append("Missing date for timeliness attribute.")
    if AttributeType.accuracy in control.attributes and "amount" not in fields:
        exceptions.append("Missing amount for accuracy attribute.")
    return exceptions


def _extract_fields_from_path(file_path: Path, safe_filename: str) -> Dict[str, str]:
    if not safe_filename.lower().endswith((".txt", ".csv")):
        return {}
    try:
        content = file_path.read_bytes()
    except OSError:
        return {}
    return _extract_fields(safe_filename, content)


@app.post("/evidence/upload", response_model=EvidenceMetadata)
def upload_evidence(
    file: UploadFile = File(...),
    control_id: Optional[str] = None,
    notes: Optional[str] = None,
) -> EvidenceMetadata:
    if control_id and control_id not in CONTROLS:
        raise HTTPException(status_code=404, detail="Control not found")
    evidence_id = str(uuid4())
    safe_filename = Path(file.filename).name if file.filename else "upload.bin"
    evidence_path = EVIDENCE_DIR / f"{evidence_id}_{safe_filename}"
    sha256 = hashlib.sha256()
    size_bytes = 0
    try:
        with evidence_path.open("wb") as handle:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                size_bytes += len(chunk)
                if size_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="Upload exceeds 50MB limit")
                sha256.update(chunk)
                handle.write(chunk)
    except HTTPException:
        if evidence_path.exists():
            evidence_path.unlink()
        raise

    if size_bytes == 0:
        if evidence_path.exists():
            evidence_path.unlink()
        raise HTTPException(status_code=400, detail="Empty file upload")

    extracted_fields = _extract_fields_from_path(evidence_path, safe_filename)
    extraction_status = "complete" if extracted_fields else "accepted"
    exceptions: List[str] = []
    authenticity_score = 0.5
    authenticity_notes = "Basic heuristic placeholder."

    if control_id:
        exceptions = _cross_validate(CONTROLS[control_id], extracted_fields)

    metadata = EvidenceMetadata(
        id=evidence_id,
        filename=safe_filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        uploaded_at=datetime.utcnow(),
        linked_control_id=control_id,
        notes=notes,
        sha256=sha256.hexdigest(),
        storage_path=f"evidence/{evidence_id}_{safe_filename}",
        extracted_fields=extracted_fields,
        extraction_status=extraction_status,
        potential_exceptions=exceptions,
        authenticity_score=authenticity_score,
        authenticity_notes=authenticity_notes,
    )
    EVIDENCE[evidence_id] = metadata
    return metadata


@app.get("/evidence", response_model=List[EvidenceMetadata])
def list_evidence() -> List[EvidenceMetadata]:
    return list(EVIDENCE.values())


@app.get("/evidence/{evidence_id}/download")
def download_evidence(evidence_id: str) -> FileResponse:
    metadata = EVIDENCE.get(evidence_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Evidence not found")
    evidence_path = EVIDENCE_DIR / f"{evidence_id}_{metadata.filename}"
    if not evidence_path.exists():
        raise HTTPException(status_code=404, detail="Evidence file missing")
    return FileResponse(
        evidence_path,
        media_type=metadata.content_type,
        filename=metadata.filename,
    )


@app.delete("/evidence/{evidence_id}", response_model=EvidenceMetadata)
def delete_evidence(evidence_id: str) -> EvidenceMetadata:
    metadata = EVIDENCE.pop(evidence_id, None)
    if not metadata:
        raise HTTPException(status_code=404, detail="Evidence not found")
    evidence_path = EVIDENCE_DIR / f"{evidence_id}_{metadata.filename}"
    if evidence_path.exists():
        evidence_path.unlink()
    return metadata


@app.post("/tests/run", response_model=TestRunResult)
def run_test(payload: TestRunRequest) -> TestRunResult:
    if payload.control_id not in CONTROLS:
        raise HTTPException(status_code=404, detail="Control not found")
    if not payload.evidence_ids:
        raise HTTPException(status_code=400, detail="Evidence IDs required")
    missing = [eid for eid in payload.evidence_ids if eid not in EVIDENCE]
    if missing:
        raise HTTPException(status_code=404, detail=f"Evidence not found: {missing}")

    findings = [
        TestFinding(
            attribute=attribute,
            result="pending",
            explanation="AI review pending in MVP. Reviewer to assess evidence.",
            evidence_ids=payload.evidence_ids,
        )
        for attribute in CONTROLS[payload.control_id].attributes
    ]
    test_run_id = str(uuid4())
    test_run = TestRunResult(
        id=test_run_id,
        control_id=payload.control_id,
        findings=findings,
        exceptions=[],
        created_at=datetime.utcnow(),
    )
    TEST_RUNS[test_run_id] = test_run
    return test_run


@app.get("/tests/{test_run_id}", response_model=TestRunResult)
def get_test_run(test_run_id: str) -> TestRunResult:
    test_run = TEST_RUNS.get(test_run_id)
    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")
    return test_run


@app.post("/workpapers/{test_run_id}", response_model=Workpaper)
def generate_workpaper(test_run_id: str) -> Workpaper:
    test_run = TEST_RUNS.get(test_run_id)
    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")
    workpaper_id = str(uuid4())
    summary = "Auto-generated testing memo (MVP placeholder)."
    conclusion = "Pending reviewer conclusion."
    workpaper = Workpaper(
        id=workpaper_id,
        test_run_id=test_run_id,
        summary=summary,
        conclusion=conclusion,
        created_at=datetime.utcnow(),
    )
    WORKPAPERS[workpaper_id] = workpaper
    return workpaper


@app.get("/workpapers/{workpaper_id}", response_model=Workpaper)
def get_workpaper(workpaper_id: str) -> Workpaper:
    workpaper = WORKPAPERS.get(workpaper_id)
    if not workpaper:
        raise HTTPException(status_code=404, detail="Workpaper not found")
    return workpaper
