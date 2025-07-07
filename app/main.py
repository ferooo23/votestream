from fastapi import FastAPI

app = FastAPI(title="Vote Stream")

@app.get("/health")
def health():
    return {"status": "ok"}