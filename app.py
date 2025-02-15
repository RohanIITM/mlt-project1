from pathlib import Path

from fastapi import FastAPI, HTTPException

from tasks import eval_task

app = FastAPI()


@app.post("/run")
def run_task(task: str):
    try:
        eval_task(task)
        return {"ran": task}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid task request {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Server error: {exc}")


@app.get("/read")
def read_path(path: str):
    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File: {file_path} not found!")
    return file_path.read_text()
