from pathlib import Path

from fastapi import FastAPI, HTTPException

from .tasks import eval_task

app = FastAPI()


@app.post("/run")
def run_task(task: str):
    try:
        eval_task(task)
        return {"status": "success"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task request")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/read")
def read_path(path: str):
    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return file_path.read_text()
