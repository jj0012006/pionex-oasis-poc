#!/usr/bin/env python3
"""Minimal FastAPI backend for Pionex OASIS POC"""

import os
import sys

# Print debug info BEFORE importing anything else
print(f"DEBUG: Python path: {sys.path}", flush=True)
print(f"DEBUG: PORT env var: {os.environ.get('PORT', 'NOT SET')}", flush=True)
print(f"DEBUG: Starting import...", flush=True)

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import json
import asyncio

print(f"DEBUG: Imports successful", flush=True)

app = FastAPI(title="Pionex OASIS POC", version="0.1.0", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class SimulationRequest(BaseModel):
    campaign_id: str
    scenario: str
    agents_count: Optional[int] = 50

MOCK_COMMENTS = ["🤖 Agent 分析中", "📊 数据预处理完成", "💡 推荐策略 A", "⚡ 推荐策略 B", "🎯 风险评估完成", "✅ 模拟执行成功"]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/status")
async def api_status():
    return {"service": "Pionex OASIS POC", "status": "running"}

async def simulate_stream(campaign_id: str, scenario: str):
    for i, comment in enumerate(MOCK_COMMENTS):
        yield f"data: {json.dumps({'index': i, 'content': comment})}\n\n"
        await asyncio.sleep(0.3)
    yield f"data: {json.dumps({'type': 'complete'})}\n\n"

@app.post("/api/simulate")
async def start_simulation(request: SimulationRequest):
    return StreamingResponse(simulate_stream(request.campaign_id, request.scenario), media_type="text/event-stream")
