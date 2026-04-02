#!/usr/bin/env python3
"""
Pionex OASIS - Activity Simulation Engine
Rule-based simulation for campaign performance prediction
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict
import json
import asyncio
import random

# Initialize FastAPI app
app = FastAPI(
    title="Pionex OASIS - Activity Simulation Engine",
    description="Rule-based campaign performance prediction",
    version="0.2.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== Data Models ==============

class UserSegment:
    """User segment definitions with base conversion rates"""
    SEGMENTS = {
        "new_unfunded": {
            "name": "新注册未入金",
            "base_conversion": 0.08,  # 8% 基础转化
            "avg_deposit": 150,  # 平均入金 150U
            "sensitivity": {
                "reward": 2.0,  # 对奖励敏感度高
                "threshold": 0.5,  # 对门槛敏感度低
            }
        },
        "small_deposit": {
            "name": "小额入金",
            "base_conversion": 0.12,
            "avg_deposit": 300,
            "sensitivity": {
                "reward": 1.5,
                "threshold": 1.0,
            }
        },
        "active_trader": {
            "name": "活跃交易",
            "base_conversion": 0.25,
            "avg_deposit": 1500,
            "sensitivity": {
                "reward": 0.8,
                "threshold": 1.5,
            }
        },
        "dormant": {
            "name": "沉睡用户",
            "base_conversion": 0.05,
            "avg_deposit": 200,
            "sensitivity": {
                "reward": 2.5,
                "threshold": 0.3,
            }
        }
    }

class Channel:
    """Channel definitions"""
    CHANNELS = {
        "kol_youtuber": {
            "name": "猷台人 (YouTube)",
            "user_profile": "台湾当冲散户",
            "preferred_assets": ["RWA", "ETF", "贵金属"],
            "engagement_multiplier": 1.2
        },
        "line_community": {
            "name": "當沖勒戒所 (LINE)",
            "user_profile": "当冲社群",
            "preferred_assets": ["合约", "现货"],
            "engagement_multiplier": 1.5
        }
    }

class SimulationRequest(BaseModel):
    campaign_name: str
    user_segment: str  # new_unfunded, small_deposit, active_trader, dormant
    channel: str  # kol_youtuber, line_community
    reward_amount: float  # 5, 10, 50, etc.
    reward_type: str  # first_deposit, trading_volume, lottery
    threshold: str  # none, low, medium, high
    duration_days: int
    reach: int  # 触达人数

class SimulationStep(BaseModel):
    step: int
    title: str
    content: str
    metric_type: str
    value: float
    timestamp: str

class SimulationResult(BaseModel):
    campaign_name: str
    status: str
    total_participants: int
    conversion_rate: float
    expected_volume: float
    estimated_cost: float
    roi: float
    risk_factors: List[str]
    recommendations: List[str]
    steps: List[SimulationStep]

# ============== Simulation Engine ==============

def calculate_conversion_rate(segment: str, reward: float, threshold: str, reward_type: str) -> float:
    """Calculate conversion rate based on rules"""
    seg_data = UserSegment.SEGMENTS.get(segment, UserSegment.SEGMENTS["new_unfunded"])
    base_rate = seg_data["base_conversion"]
    
    # Reward multiplier
    reward_mult = 1.0
    if reward >= 50:
        reward_mult = 2.0
    elif reward >= 20:
        reward_mult = 1.5
    elif reward >= 10:
        reward_mult = 1.2
    
    # Threshold multiplier
    threshold_mult = 1.0
    if threshold == "none":
        threshold_mult = 1.3
    elif threshold == "low":
        threshold_mult = 1.1
    elif threshold == "high":
        threshold_mult = 0.7
    
    # Reward type fit
    type_fit = 1.0
    if segment == "new_unfunded" and reward_type == "first_deposit":
        type_fit = 1.5
    elif segment == "active_trader" and reward_type == "trading_volume":
        type_fit = 1.4
    elif segment == "dormant" and reward_type == "lottery":
        type_fit = 1.3
    
    return base_rate * reward_mult * threshold_mult * type_fit

def generate_simulation_steps(request: SimulationRequest, result: dict) -> List[dict]:
    """Generate step-by-step simulation output"""
    steps = []
    now = datetime.now()
    
    # Step 1: Campaign analysis
    steps.append({
        "step": 1,
        "title": "📊 活动分析",
        "content": f"活动类型：{request.reward_type} | 奖励：${request.reward_amount} | 门槛：{request.threshold}",
        "metric_type": "analysis",
        "value": 0,
        "timestamp": now.isoformat()
    })
    
    # Step 2: Segment analysis
    seg_name = UserSegment.SEGMENTS.get(request.user_segment, {}).get("name", request.user_segment)
    steps.append({
        "step": 2,
        "title": "👥 目标用户",
        "content": f"{seg_name} | 触达：{request.reach:,} 人 | 基础转化率：{UserSegment.SEGMENTS.get(request.user_segment, {}).get('base_conversion', 0.08)*100:.1f}%",
        "metric_type": "segment",
        "value": request.reach,
        "timestamp": now.isoformat()
    })
    
    # Step 3: Channel analysis
    ch_name = Channel.CHANNELS.get(request.channel, {}).get("name", request.channel)
    ch_mult = Channel.CHANNELS.get(request.channel, {}).get("engagement_multiplier", 1.0)
    steps.append({
        "step": 3,
        "title": "📢 渠道分析",
        "content": f"{ch_name} | 参与度系数：{ch_mult}x",
        "metric_type": "channel",
        "value": ch_mult,
        "timestamp": now.isoformat()
    })
    
    # Step 4: Conversion calculation
    steps.append({
        "step": 4,
        "title": "🎯 预期转化",
        "content": f"调整后转化率：{result['conversion_rate']*100:.2f}% | 预期参与：{result['total_participants']:,} 人",
        "metric_type": "conversion",
        "value": result['conversion_rate'],
        "timestamp": now.isoformat()
    })
    
    # Step 5: Volume projection
    steps.append({
        "step": 5,
        "title": "💰 交易量预测",
        "content": f"预期交易量：${result['expected_volume']:,.0f} | 人均：${result['expected_volume']/max(result['total_participants'],1):,.0f}",
        "metric_type": "volume",
        "value": result['expected_volume'],
        "timestamp": now.isoformat()
    })
    
    # Step 6: ROI calculation
    steps.append({
        "step": 6,
        "title": "📈 ROI 分析",
        "content": f"预计成本：${result['estimated_cost']:,.0f} | ROI: {result['roi']*100:.1f}%",
        "metric_type": "roi",
        "value": result['roi'],
        "timestamp": now.isoformat()
    })
    
    # Step 7: Risk assessment
    risk_count = len(result['risk_factors'])
    steps.append({
        "step": 7,
        "title": "⚠️ 风险评估",
        "content": f"识别 {risk_count} 个风险点 | 建议：{result['recommendations'][0] if result['recommendations'] else '无'}",
        "metric_type": "risk",
        "value": risk_count,
        "timestamp": now.isoformat()
    })
    
    # Step 8: Complete
    steps.append({
        "step": 8,
        "title": "✅ 模拟完成",
        "content": f"完整报告已生成 | 预期参与 {result['total_participants']:,} 人 | ROI {result['roi']*100:.1f}%",
        "metric_type": "complete",
        "value": 1.0,
        "timestamp": now.isoformat()
    })
    
    return steps

def generate_risk_factors(request: SimulationRequest, result: dict) -> List[str]:
    """Generate risk factors based on simulation"""
    risks = []
    
    if request.reward_amount >= 50:
        risks.append("高奖励可能吸引羊毛党")
    if request.threshold == "none":
        risks.append("无门槛可能导致低质量转化")
    if request.duration_days > 14:
        risks.append("活动周期过长可能稀释紧迫感")
    if result['roi'] < 1.0:
        risks.append("ROI 低于 1，建议优化奖励结构")
    if request.reach > 10000:
        risks.append("大规模触达需确认预算充足")
    
    return risks if risks else ["无明显风险"]

def generate_recommendations(request: SimulationRequest, result: dict) -> List[str]:
    """Generate recommendations"""
    recs = []
    
    if result['roi'] < 2.0:
        recs.append("考虑降低奖励金额或提高门槛")
    if request.user_segment == "new_unfunded":
        recs.append("新户建议配合教育内容提高留存")
    if request.channel == "kol_youtuber":
        recs.append("YouTube 渠道建议制作专题视频")
    if request.reward_type == "lottery":
        recs.append("抽奖活动需明确中奖概率公示")
    
    recs.append("建议 A/B 测试不同奖励档位")
    
    return recs

# ============== API Endpoints ==============

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.2.0"
    }

@app.get("/api/status")
async def api_status():
    return {
        "service": "Pionex OASIS - Activity Simulation Engine",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/segments")
async def get_segments():
    """Get available user segments"""
    return {
        "segments": [
            {"id": k, "name": v["name"], "base_conversion": v["base_conversion"]}
            for k, v in UserSegment.SEGMENTS.items()
        ]
    }

@app.get("/api/channels")
async def get_channels():
    """Get available channels"""
    return {
        "channels": [
            {"id": k, "name": v["name"], "user_profile": v["user_profile"]}
            for k, v in Channel.CHANNELS.items()
        ]
    }

@app.post("/api/simulate")
async def start_simulation(request: SimulationRequest):
    """Run activity simulation with streaming results"""
    
    # Calculate metrics
    conversion_rate = calculate_conversion_rate(
        request.user_segment,
        request.reward_amount,
        request.threshold,
        request.reward_type
    )
    
    # Apply channel multiplier
    channel_mult = Channel.CHANNELS.get(request.channel, {}).get("engagement_multiplier", 1.0)
    conversion_rate *= channel_mult
    
    total_participants = int(request.reach * conversion_rate)
    avg_deposit = UserSegment.SEGMENTS.get(request.user_segment, {}).get("avg_deposit", 150)
    expected_volume = total_participants * avg_deposit
    estimated_cost = total_participants * request.reward_amount
    roi = expected_volume / max(estimated_cost, 1)
    
    # Generate risk factors and recommendations
    result = {
        "conversion_rate": conversion_rate,
        "total_participants": total_participants,
        "expected_volume": expected_volume,
        "estimated_cost": estimated_cost,
        "roi": roi,
        "risk_factors": [],
        "recommendations": []
    }
    
    result["risk_factors"] = generate_risk_factors(request, result)
    result["recommendations"] = generate_recommendations(request, result)
    
    # Generate steps
    steps = generate_simulation_steps(request, result)
    
    # Stream steps
    async def simulate_stream():
        for step in steps:
            data = {
                "type": "step",
                "content": step,
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.5)
        
        # Final result
        final_data = {
            "type": "complete",
            "result": {
                "campaign_name": request.campaign_name,
                "total_participants": total_participants,
                "conversion_rate": f"{conversion_rate*100:.2f}%",
                "expected_volume": f"${expected_volume:,.0f}",
                "estimated_cost": f"${estimated_cost:,.0f}",
                "roi": f"{roi*100:.1f}%",
                "risk_factors": result["risk_factors"],
                "recommendations": result["recommendations"]
            },
            "timestamp": datetime.now().isoformat()
        }
        yield f"data: {json.dumps(final_data)}\n\n"
    
    return StreamingResponse(
        simulate_stream(),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
