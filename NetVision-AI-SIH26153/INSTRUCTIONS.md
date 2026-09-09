# NetVision AI — Project Instructions

## 1. Requirements

Make sure the following are installed:

- Python 3.13
- Node.js
- npm
- Git

The project uses the Python virtual environment:

```text
.venv313

==========================================================
2. Project Root

Open the terminal in the project root.

The project root is the folder containing:

backend/
frontend/
models/
src/
tests/
requirements.txt

========================================

3. Start the Backend

Open Terminal 1 in the project root.

-> Activate the Python environment

Windows PowerShell
.\.venv313\Scripts\Activate.ps1

Windows CMD
.venv313\Scripts\activate

Git Bash
source .venv313/Scripts/activate

After activation, you should see:

(.venv313)

-> Start FastAPI
python -m uvicorn backend.app.main:app --reload

The backend will run at:

http://127.0.0.1:8000

Keep Terminal 1 running.

=================================================================

4. Check the Backend

Open this in your browser:

http://127.0.0.1:8000

The backend should show:

NetVision AI
Network Attack Forecasting

Then check: http://127.0.0.1:8000/health

The health status should be:  healthy

The response should show that these components are loaded:

ML Model
World Model
XAI
MITRE ATT&CK

=====================================================================

5. Start the Frontend

Open Terminal 2.

Go to the project root and then enter the frontend directory:  cd frontend

If dependencies have not been installed yet: npm install

Start the frontend: npm run dev

Vite will display a local URL, normally:

http://localhost:5173

Open the URL shown by Vite in your browser.

Keep Terminal 2 running.

=========================================================