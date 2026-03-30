#!/usr/bin/env python3
"""
Phase 2 Backend Service for Pionex OASIS POC
FastAPI backend for serving simulation results and managing test campaigns
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import json
import asyncio
import os

# Validate required environment variables at startup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("⚠️ WARNING: OPENAI_API_KEY is not set! Service will start but API calls will fail.")
    print("⚠️ Please set OPENAI_API_KEY in Railway Variables dashboard.")
else:
    print(f"✅ OPENAI_API_KEY is configured (length: {len(OPENAI_API_KEY)})")
    # Don't initialize OpenAI client at startup - will do it lazily when needed
    # This avoids blocking the startup process
    print("ℹ️ OpenAI client will be initialized on first use")

# Initialize FastAPI app
app = FastAPI(
    title="Pionex OASIS POC - Phase 2 Backend",
    description="Backend service for managing simulations and campaigns",
    version="0.1.0"
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
class HealthStatus(BaseModel):
    status: str
    timestamp: str
    version: str

class SimulationRequest(BaseModel):
    campaign_id: str
    scenario: str
    agents_count: Optional[int] = 100

# Mock comments for streaming simulation
MOCK_COMMENTS = [
    "🤖 Agent 分析中：已識別活動類型為 {campaign_id}",
    "📊 數據預處理完成，檢測到場景：{scenario}",
    "💡 推薦策略 A：基於歷史數據的最優解",
    "⚡ 推薦策略 B：風險最小化方案",
    "🎯 風險評估完成：總體風險等級為中等",
    "✅ 模擬執行成功，預期收益範圍：10% - 25%",
    "📈 回測完成：歷史勝率 78%，最大回撤 -12%",
    "🔔 警告：建議在非高波動時段執行",
    "✨ Agent 評估完成，準備就緒！"
]

# Async generator for SSE streaming
async def simulate_stream(campaign_id: str, scenario: str):
    """
    Async generator that yields SSE formatted comments
    """
    for comment in MOCK_COMMENTS:
        # Format comment with campaign_id and scenario
        formatted_comment = comment.format(campaign_id=campaign_id, scenario=scenario)

        # Yield SSE formatted data
        data = {
            "type": "comment",
            "content": formatted_comment,
            "timestamp": datetime.now().isoformat()
        }
        yield f"data: {json.dumps(data)}\n\n"

        # Wait 0.3 seconds before next message
        await asyncio.sleep(0.3)

    # Final completion message
    final_data = {
        "type": "complete",
        "message": "模擬完成！",
        "timestamp": datetime.now().isoformat()
    }
    yield f"data: {json.dumps(final_data)}\n\n"

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0"
    }

@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    return {
        "service": "Pionex OASIS POC Phase 2",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/simulate")
async def start_simulation(request: SimulationRequest):
    """Start a new simulation with SSE streaming"""
    return StreamingResponse(
        simulate_stream(request.campaign_id, request.scenario),
        media_type="text/event-stream"
    )

@app.get("/api/results/{campaign_id}")
async def get_results(campaign_id: str):
    """Get simulation results"""
    return {
        "campaign_id": campaign_id,
        "status": "completed",
        "message": "Results would be retrieved from storage"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
