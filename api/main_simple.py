from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json, asyncio, os

print(f"DEBUG: Starting on port {os.environ.get('PORT', 8000)}", flush=True)

app = FastAPI(docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health(): return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/status")
def status(): return {"status": "running"}

@app.post("/api/simulate")
async def simulate(req: dict):
    async def gen():
        for i in range(5):
            yield f"data: {json.dumps({'i': i})}\n\n"
            await asyncio.sleep(0.2)
    return StreamingResponse(gen(), media_type="text/event-stream")
