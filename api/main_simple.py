#!/usr/bin/env python3
"""Minimal FastAPI backend for Pionex OASIS POC"""

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import json
import asyncio
import os
import sys

# Get port from environment variable (Railway sets this)
PORT = int(os.environ.get("PORT", 8000))
print(f"DEBUG: Starting server on port {PORT}", file=sys.stderr, flush=True)

app = FastAPI(title="Pionex OASIS POC", version="0.1.0", docs_url=None, redoc_url=None)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class SimulationRequest(BaseModel):
    campaign_id: str
    scenario: str
    agents_count: Optional[int] = 50

MOCK_COMMENTS = ["🤖 Agent 分析中", "📊 数据预处理完成", "💡 推荐策略 A", "⚡ 推荐策略 B", "🎯 风险评估完成", "✅ 模拟执行成功", "✨ Agent 评估完成"]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "port": PORT, "timestamp": datetime.now().isoformat()}

@app.get("/api/status")
async def api_status():
    return {"service": "Pionex OASIS POC", "status": "running", "port": PORT}

async def simulate_stream(campaign_id: str, scenario: str):
    for i, comment in enumerate(MOCK_COMMENTS):
        yield f"data: {json.dumps({'index': i, 'content': comment})}\n\n"
        await asyncio.sleep(0.3)
    yield f"data: {json.dumps({'type': 'complete', 'total': len(MOCK_COMMENTS)})}\n\n"

@app.post("/api/simulate")
async def start_simulation(request: SimulationRequest):
    return StreamingResponse(simulate_stream(request.campaign_id, request.scenario), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})

if __name__ == "__main__":
    import uvicorn
    print(f"DEBUG: Listening on 0.0.0.0:{PORT}", file=sys.stderr, flush=True)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
