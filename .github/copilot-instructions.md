# Copilot / AI Agent Instructions (Auto-Healing Backend)

## 🧠 Big picture
This repo is a tiny Flask-based “auto-healing” webhook receiver. It listens for alerts (e.g., Prometheus Alertmanager) and performs simple remediation by running `docker` commands against a container named `myapp`.

## 📦 Key files
- `app.py.txt` — main Flask service. Contains the webhook route and action logic.
- `requirements.txt.txt` — Python deps (Flask + boto3/requests/dotenv are installed even if not currently used).

## 🚀 How to run (developer workflow)
1. Create a virtualenv and install deps:
   - `python -m venv .venv`
   - Windows: `.\.venv\Scripts\activate`
   - `python -m pip install -r requirements.txt.txt`
2. Start the service:
   - `python app.py.txt`
3. The service listens on `0.0.0.0:5000` and exposes:
   - `POST /webhook` (main alert receiver)
   - `GET  /simulate` (manual restart shortcut)

> Note: The code uses `os.system("docker ...")`. Ensure Docker is installed and a container named `myapp` exists.

## 🔍 What the webhook expects (inferred from the code)
The handler assumes a Prometheus/Alertmanager-style payload (visible in `app.py.txt`):
```json
{ "alerts": [{ "labels": { "alertname": "HighCPU" } }] }
```
The action is chosen based on `alertname`.

## 🧩 How to extend / modify actions
- Update `app.py.txt` `webhook()` handler to add new alert names or change behavior.
- If you need richer logic, replace `os.system("docker ...")` with a proper Docker SDK call or a new helper module.

## 🧭 Conventions / patterns in this repo
- Minimal single-file service (no packages, no blueprints).
- Uses `os.system(...)` for side effects (Docker CLI). Keep it simple; avoid adding layered abstractions unless you need them.
- No tests exist currently; changes should be validated by running the service and calling the endpoints.

## 🔌 Integration points / external dependencies
- Docker engine (required for `docker restart` / `docker start` commands)
- The service is designed to be called by an external alerting system (Prometheus Alertmanager or similar).

---

If anything about the alert payload shape, Docker container naming, or run/debug workflow is unclear, point me to the part you want expanded and I’ll adjust the instructions.