"""Pionex OASIS - Minimal FastAPI Backend"""
import os, json, asyncio
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Get port from Railway environment variable
PORT = int(os.environ.get('PORT', 8000))
print(f"=== DEBUG: Starting server on port {PORT} ===", flush=True)

app = FastAPI(title="Pionex OASIS", version="0.1.0", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class SimRequest(BaseModel):
    campaign_id: str = "default"
    scenario: str = "all"
    agents_count: Optional[int] = 50

@app.get("/health")
def health():
    return {"status": "healthy", "port": PORT, "timestamp": datetime.now().isoformat()}

@app.get("/api/status")
def status():
    return {"status": "running", "port": PORT}

@app.get("/")
def root():
    return {"message": "Pionex OASIS API", "version": "0.1.0", "port": PORT}

@app.post("/api/simulate")
async def simulate(req: SimRequest):
    async def gen():
        comments = ["🤖 Agent 分析中", "📊 数据处理", "💡 生成建议", "✅ 完成"]
        for i, c in enumerate(comments):
            yield f"data: {json.dumps({'i': i, 'content': c})}\n\n"
            await asyncio.sleep(0.3)
        yield f"data: {json.dumps({'type': 'complete', 'total': len(comments)})}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})

if __name__ == "__main__":
    import uvicorn
    print(f"=== DEBUG: Listening on 0.0.0.0:{PORT} ===", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
