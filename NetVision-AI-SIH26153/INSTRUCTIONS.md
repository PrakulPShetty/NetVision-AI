# NetVision AI: Run Instructions

## Requirements

- Python 3.11 or newer (Python 3.13 recommended)
- Node.js 18 or newer and npm
- Git

Run the commands below from the application project directory: the directory
containing `backend/`, `frontend/`, `models/`, `src/`, `tests/`, and
`requirements.txt`. In this repository, that directory is
`NetVision-AI-SIH26153/` beneath the repository root.

## One-time setup

From the application project directory, create and prepare the Python
environment and install frontend dependencies:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cd frontend
npm install
cd ..
```

If Python 3.13 is unavailable, use `python -m venv .venv` instead of the
`py -3.13` command, provided the installed Python version is 3.11 or newer.

## Start the backend

Open Terminal 1 in the application project directory, activate the environment,
and start FastAPI:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

The API is at `http://127.0.0.1:8000`. Check `http://127.0.0.1:8000/health`
for model and service status, and `http://127.0.0.1:8000/docs` for the API docs.
Keep Terminal 1 running.

## Start the frontend

Open Terminal 2 in the application project directory and run:

```powershell
cd frontend
npm run dev
```

Open the URL printed by Vite (normally `http://localhost:5173`) and keep
Terminal 2 running. The dashboard connects to the backend on port 8000.

## Start both services with the runner

Alternatively, from the application project directory with `.venv` activated
and frontend dependencies installed, run:

```powershell
python run_all.py --serve
```

The runner starts both services. Press `Ctrl+C` in that terminal to stop them.
