#!/usr/bin/env python3
"""
Minimal FastAPI backend for Pionex OASIS POC
No lifespan events, no blocking initialization
"""

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import json
import asyncio

# Initialize FastAPI app WITHOUT any startup events
app = FastAPI(
    title="Pionex OASIS POC - Minimal",
    description="Minimal backend service for testing",
    version="0.1.0",
    # Disable automatic docs to reduce startup time
    docs_url=None,
    redoc_url=None,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class SimulationRequest(BaseModel):
    campaign_id: str
    scenario: str
    agents_count: Optional[int] = 50

# Mock comments for streaming
MOCK_COMMENTS = [
    "🤖 Agent 分析中：已识别活动类型",
    "📊 数据预处理完成",
    "💡 推荐策略 A：基于历史数据",
    "⚡ 推荐策略 B：风险最小化",
    "🎯 风险评估完成",
    "✅ 模拟执行成功",
    "📈 回测完成：历史胜率 78%",
    "✨ Agent 评估完成",
]

@app.get("/health")
async def health_check():
    """Health check endpoint - MUST respond quickly for Railway"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0-minimal"
    }

@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    return {
        "service": "Pionex OASIS POC - Minimal",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

async def simulate_stream(campaign_id: str, scenario: str):
    """Async generator for SSE streaming"""
    for i, comment in enumerate(MOCK_COMMENTS):
        data = json.dumps({
            "index": i,
            "type": "comment",
            "content": comment,
            "timestamp": datetime.now().isoformat()
        })
        yield f"data: {data}\n\n"
        await asyncio.sleep(0.3)
    
    # Send completion message
    data = json.dumps({
        "type": "complete",
        "total_comments": len(MOCK_COMMENTS),
        "timestamp": datetime.now().isoformat()
    })
    yield f"data: {data}\n\n"

@app.post("/api/simulate")
async def start_simulation(request: SimulationRequest):
    """Start simulation with SSE streaming"""
    return StreamingResponse(
        simulate_stream(request.campaign_id, request.scenario),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# Simple entry point for Railway
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
