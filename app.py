from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy", "time": datetime.now().isoformat()}

@app.get("/")
def root():
    return {"message": "Hello from Railway!"}
