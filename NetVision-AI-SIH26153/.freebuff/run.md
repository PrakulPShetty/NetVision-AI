# NetVision AI — Preview Run Doc

Workspace root: `C:\Users\ASUS\OneDrive\ドキュメント\GitHub\NetVision-AI-SIH26153\NetVision-AI-SIH26153`
This workspace IS the main checkout (no worktree copying needed). Ports 3000 (frontend) and 8000 (backend).

## 1. Reproduce uncommitted artifacts

Uncommitted state (git status): the frontend uses the ORIGINAL brand asset, which is
**untracked** — a fresh checkout of the committed tree would not have it. Reproduce with:

1. Copy the original logo into the served public folder (byte-for-byte, no editing):
   ```
   cp "design-reference/branding/netvision updated logo.png" "frontend/public/brand/netvision-logo.png"
   ```
   (`frontend/src/components/common/Brand.jsx` is committed-referenced as `/brand/netvision-logo.png`
   and `frontend/index.html` references `/brand/netvision-favicon.png`; the favicon is a
   64x64 crop of the original's emblem — regenerate with System.Drawing if missing.)

2. Uncommitted frontend source: `frontend/src/components/common/Brand.jsx`,
   `frontend/src/components/home/NetworkCanvas.jsx`, `frontend/src/components/layout/SiteNav.jsx`,
   `frontend/src/pages/HomePage.jsx`, `frontend/src/index.css`, `frontend/index.html`.
   These exist in the working tree; nothing else to regenerate. Build check: `npm run build` in `frontend/`.

3. Environment files: none required. Backend reads no `.env`; frontend talks to
   `http://localhost:8000` via the vite proxy (`/api` -> `127.0.0.1:8000`) and direct health checks.

## 2. Run the servers

Backend (FastAPI + ML models, ~10s startup while models load):

```
cd <workspace root>
nohup .venv/Scripts/python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 > backend-uvicorn.log 2>&1 &
```

Verify: `curl http://127.0.0.1:8000/health` →
`{"status":"healthy","ml_model":"loaded","world_model":"loaded","xai":"loaded","mitre_attack":"loaded"}`

Frontend (vite dev, port 3000 configured in `frontend/vite.config.js`) — Windows detached recipe:

```
powershell -NoProfile -Command "(Start-Process -FilePath 'npm.cmd' -ArgumentList 'run','dev' -WorkingDirectory '<workspace root>\frontend' -RedirectStandardOutput '<workspace root>\.freebuff\preview-05d7f751-9b1d-41ef-9c1c-e2f7afa53b01.log' -RedirectStandardError '<workspace root>\.freebuff\preview-05d7f751-9b1d-41ef-9c1c-e2f7afa53b01.log.err' -WindowStyle Hidden -PassThru).Id"
```

- stdout and stderr go to DIFFERENT files (`...log` and `...log.err`) — PowerShell requires this.
- The Start-Process call can hang until timeout; check `netstat -ano | findstr :3000` —
  the server usually starts anyway. Confirm the pid: `powershell -NoProfile -Command "Get-Process -Id <pid>"`.
- Wait for HTTP 200 on `http://localhost:3000/` before registering the preview.

Register: preview URL `http://localhost:3000/`, pid = the printed npm/node process id.

## Health signals in the UI

- Navbar status pill: `FORECAST ENGINE ONLINE` (green dot) = backend reachable.
- Footer: `Engine: online`.
- A full analysis flow: Analyze page → pick a scenario card → "Analyze network" →
  auto-navigates to Forecast with real model output (ensemble %, Markov horizons, SHAP, ATT&CK).
