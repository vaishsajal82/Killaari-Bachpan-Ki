"""
run.py — convenience entrypoint for local development.
    python run.py
For production, use a real ASGI server invocation instead, e.g.:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
