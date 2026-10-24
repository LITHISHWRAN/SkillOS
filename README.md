# SkillOs

SkillOs is an open-source workbench for creating, validating, reviewing, and improving Agent Skills.

## MVP capabilities

- Generate `SKILL.md` content using an OpenAI-compatible model endpoint.
- Validate Agent Skills frontmatter and common specification constraints.
- Scan skill text with transparent heuristic security rules.
- Request an AI quality review.
- Improve a draft using review findings.
- Export the current `SKILL.md` from the browser.

## Architecture

- `backend/`: FastAPI, PyYAML validation, heuristic scanning, OpenAI-compatible inference client.
- `frontend/`: React + TypeScript + Vite.
- `examples/`: example skill fixture.
- `backend/tests/`: automated backend tests.

The validator follows the public Agent Skills format as documented at https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx. Check the current specification before releasing changes; standards can evolve.

## Requirements

- Python 3.10+
- Node.js 20+
- A running OpenAI-compatible chat-completions endpoint for AI generation/review. Local `llama.cpp` server is supported. A compatible hosted endpoint can also be configured.

## Run the backend (Windows PowerShell)

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env if your model endpoint/model name differs.
uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

## Run tests

In the backend directory, with the virtual environment active:

```powershell
$env:PYTHONPATH = "."
pytest -q
```

## Configure llama.cpp

Start a compatible `llama-server` with your model. For example, adjust the model path and options to your installed llama.cpp build:

```powershell
llama-server.exe -m "C:\models\your-model.gguf" --host 127.0.0.1 --port 8080
```

Then set in `backend/.env`:

```dotenv
LLM_BASE_URL=http://127.0.0.1:8080/v1
LLM_API_KEY=
LLM_MODEL=assistant
```

The server's advertised model identifier can vary by configuration. If requests fail, inspect the llama-server logs and `/v1/models`, then set `LLM_MODEL` to the identifier it expects. Do not expose the local inference server publicly.

## Run the frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local Vite URL printed by the command (normally http://localhost:5173).

If your backend is hosted elsewhere, set `VITE_API_BASE_URL` in `frontend/.env.local`, for example:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## API endpoints

- `GET /api/health`
- `POST /api/validate` — JSON `{ "content": "...", "directory_name": "optional-folder-name" }`
- `POST /api/security-scan` — same request shape; never executes submitted content.
- `POST /api/review` — validates and sends content to the configured model.
- `POST /api/generate` — JSON `{ "task": "...", "model_instructions": "optional" }`
- `POST /api/improve` — JSON `{ "content": "...", "findings": ["..."], "intended_behavior": "optional" }`

## Security notes

- AI reviews and security checks are advisory.
- The scanner uses heuristics and can have false positives and false negatives.
- Uploaded or pasted skill scripts are never executed.
- Keep `.env` and API keys out of Git.
- Do not expose the development API publicly without authentication, request limits, and production hardening.
- The model receives the supplied skill text. Do not send confidential content to a hosted provider unless permitted.
- Review generated skills before installing or executing their bundled scripts.

## Current limitations

- This MVP edits a single `SKILL.md` at a time; it does not yet ingest or export complete skill folders.
- It does not execute or sandbox skill scripts.
- The security scanner is rule-based and not a comprehensive security product.
- Model review requires an available OpenAI-compatible endpoint.
- The initial frontend test checks test-runner setup; the backend tests cover core validation and scanning behavior.
