from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="OMML to LaTeX Microservice",
    description="Receives Word OMML equation XML and returns LaTeX.",
    version="1.0.0",
)

# Allow all origins for now (it's an internal service anyway).
# Later you can lock this down.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your Node server origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OmmlRequest(BaseModel):
    omml: str                 # raw OMML xml (string)
    meta: Optional[dict] = None  # optional extra info (question id etc.)


class LatexResponse(BaseModel):
    latex: str
    success: bool = True
    error: Optional[str] = None


def convert_omml_to_latex_dummy(omml_xml: str) -> str:
    """
    TEMP PLACEHOLDER:
    Right now this just wraps the OMML in $$ ... $$ so you can
    test the full pipeline wiring.

    Later you will replace this with REAL OMML → LaTeX logic using:
      - Pandoc, or
      - omml2mathml + mathml2latex, or
      - any other Python OMML converter.
    """
    # TODO: Replace with real conversion
    safe_preview = omml_xml.strip().replace("\n", " ")[:120]
    return f"$$\\text{{OMML snippet: {safe_preview} ...}}$$"


@app.post("/omml-to-latex", response_model=LatexResponse)
async def omml_to_latex_endpoint(payload: OmmlRequest):
    """
    Accepts a JSON payload like:
      { "omml": "<m:oMathPara>...</m:oMathPara>" }

    Returns:
      { "latex": "...", "success": true/false, "error": null or message }
    """
    try:
        if not payload.omml.strip():
            return LatexResponse(
                latex="",
                success=False,
                error="Empty OMML content",
            )

        latex = convert_omml_to_latex_dummy(payload.omml)
        return LatexResponse(latex=latex, success=True)

    except Exception as e:
        return LatexResponse(
            latex="",
            success=False,
            error=str(e),
        )


@app.get("/")
async def root():
    return {"message": "OMML-to-LaTeX service running"}
