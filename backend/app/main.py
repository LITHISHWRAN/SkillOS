from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os

from . import config
from .schemas import SkillTextRequest, GenerateRequest, ImproveRequest
from .services import validate_skill, scan_security, review_skill, generate_skill, improve_skill

app = FastAPI(
    title="SkillForge API",
    description="Create, validate, review, and improve Agent Skills.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "provider": "gemini",
        "model": os.getenv(
            "GEMINI_MODEL",
            "gemma-4-26b-a4b-it"
        )
    }
    
@app.post("/api/validate")
def validate(request: SkillTextRequest):
    return validate_skill(request.content, request.directory_name)

@app.post("/api/security-scan")
def security_scan(request: SkillTextRequest):
    return {"findings": scan_security(request.content), "notice": "Heuristic warnings only; no uploaded content was executed."}

@app.post("/api/review")
async def review(request: SkillTextRequest):
    validation = validate_skill(request.content, request.directory_name)
    security = scan_security(request.content)
    try:
        result = await review_skill(request.content, validation, security)
        return {"validation": validation, "security": security, "review": result}
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Model review failed: {str(exc)}") from exc


@app.post("/api/generate")
async def generate(request: GenerateRequest):
    try:
        content = await generate_skill(
            task=request.task,
            extra_instructions=request.model_instructions,
        )

        validation = validate_skill(content)

        if not validation["valid"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Generated skill failed validation.",
                    "findings": validation["findings"],
                },
            )

        return {
            "content": content,
            "validation": validation,
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except (httpx.HTTPError, RuntimeError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Skill generation failed: {str(exc)}",
        ) from exc


@app.post("/api/improve")
async def improve(request: ImproveRequest):
    try:
        content = await improve_skill(request.content, request.findings, request.intended_behavior)
        validation = validate_skill(content)
        security = scan_security(content)
        return {"content": content, "validation": validation, "security": security}
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Skill improvement failed: {str(exc)}") from exc
