# OMML to LaTeX Microservice

Small FastAPI service that accepts Word OMML equation XML and responds with LaTeX. It is currently wired with a dummy converter so you can validate the end-to-end pipeline before dropping in a real OMML→LaTeX implementation.

## Prerequisites
- Python 3.11+
- Optional: `python -m venv venv` to keep dependencies isolated

## Installation
```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
```

## Running the API
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
The service defaults to `http://127.0.0.1:8000`. The FastAPI docs UI is available at `/docs`.

## API Endpoints
- `GET /` – Health check returning `{ "message": "OMML-to-LaTeX service running" }`.
- `POST /omml-to-latex` – Accepts JSON body:
  ```json
  {
    "omml": "<m:oMathPara>...</m:oMathPara>",
    "meta": {
      "questionId": "1234"
    }
  }
  ```
  Sample response:
  ```json
  {
    "latex": "$$\\text{OMML snippet: <m:oMathPara> ...}$$",
    "success": true,
    "error": null
  }
  ```

## Notes
- CORS is open to all origins by default because this service is expected to sit behind internal infrastructure. Tighten the `allow_origins` list in `main.py` before exposing it publicly.
- `convert_omml_to_latex_dummy` currently just wraps a shortened OMML preview in `$$...$$`. Replace this function with a real converter (e.g., Pandoc or omml→mathml→latex pipeline) when ready.
- Error responses follow the `LatexResponse` schema with `success: false` and an `error` message explaining what went wrong.

## Development Tips
- Run `uvicorn main:app --reload` for hot reloading while iterating on the converter.
- Add unit tests around the real converter logic once implemented; the FastAPI endpoint can then serve as a thin transport wrapper.
