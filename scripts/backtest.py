"""
Pionex OASIS 历史活动回测脚本
将模拟结果与历史真实数据对比，输出方向一致性评分。
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# 复用主模拟脚本的核心函数
from run_simulation import (
    ROOT_DIR,
    RESULTS_DIR,
    analyze_results,
    build_activity_text,
    classify_sentiment,
    generate_agents,
    load_personas,
    simulate_agent_response,
)
from openai import OpenAI

load_dotenv()


def calculate_direction_score(simulated: dict, actual: dict) -> dict:
    """
    计算模拟结果与真实数据的方向一致性评分（0-100）

    评分维度：
    1. 参与率方向（40分）：模拟参与率与真实参与率的偏差
    2. 情绪分布方向（40分）：正面/中性/负面比例的偏差
    3. 主导情绪一致（20分）：最高占比情绪是否一致
    """
    score = 0.0
    details = {}

    # 1. 参与率偏差（40分）
    sim_rate = simulated["participation_rate"]
    actual_rate = actual["participation_rate"]
    rate_diff = abs(sim_rate - actual_rate)

    if rate_diff <= 0.05:
        rate_score = 40  # 偏差 ≤5%，满分
    elif rate_diff <= 0.10:
        rate_score = 30
    elif rate_diff <= 0.20:
        rate_score = 20
    elif rate_diff <= 0.30:
        rate_score = 10
    else:
        rate_score = 0

    score += rate_score
    details["participation_rate"] = {
        "simulated": round(sim_rate, 3),
        "actual": round(actual_rate, 3),
        "diff": round(rate_diff, 3),
        "score": rate_score,
        "max_score": 40,
    }

    # 2. 情绪分布偏差（40分）
    sim_sent = simulated["sentiment_percentages"]
    actual_sent = actual["sentiment_distribution"]
    # 将实际数据转换为百分比
    actual_pct = {k: round(v * 100, 1) for k, v in actual_sent.items()}

    sentiment_diffs = {}
    total_sent_diff = 0
    for key in ["positive", "neutral", "negative"]:
        diff = abs(sim_sent.get(key, 0) - actual_pct.get(key, 0))
        sentiment_diffs[key] = round(diff, 1)
        total_sent_diff += diff

    # 平均情绪偏差
    avg_sent_diff = total_sent_diff / 3
    if avg_sent_diff <= 5:
        sent_score = 40
    elif avg_sent_diff <= 10:
        sent_score = 30
    elif avg_sent_diff <= 20:
        sent_score = 20
    elif avg_sent_diff <= 30:
        sent_score = 10
    else:
        sent_score = 0

    score += sent_score
    details["sentiment_distribution"] = {
        "simulated": sim_sent,
        "actual": actual_pct,
        "diffs": sentiment_diffs,
        "avg_diff": round(avg_sent_diff, 1),
        "score": sent_score,
        "max_score": 40,
    }

    # 3. 主导情绪一致性（20分）
    sim_dominant = max(sim_sent, key=sim_sent.get)
    actual_dominant = max(actual_pct, key=actual_pct.get)
    dominant_match = sim_dominant == actual_dominant
    dominant_score = 20 if dominant_match else 0

    score += dominant_score
    details["dominant_sentiment"] = {
        "simulated": sim_dominant,
        "actual": actual_dominant,
        "match": dominant_match,
        "score": dominant_score,
        "max_score": 20,
    }

    return {
        "total_score": round(score),
        "max_score": 100,
        "verdict": "GO" if score >= 70 else "NO-GO",
        "details": details,
    }


def print_backtest_report(scoring: dict, activity_name: str, simulated: dict):
    """打印回测报告"""
    print("\n" + "=" * 60)
    print(f"📊 回測報告：{activity_name}")
    print("=" * 60)

    verdict = scoring["verdict"]
    total = scoring["total_score"]
    emoji = "✅" if verdict == "GO" else "❌"

    print(f"\n{emoji} 方向一致性評分：{total}/100")
    print(f"{'=' * 40}")
    print(f"   判定結果：{verdict}")
    print(f"   （≥70 為 GO，<70 為 NO-GO）")

    print("\n📋 評分明細：")

    # 参与率
    pr = scoring["details"]["participation_rate"]
    print(f"\n  1️⃣ 參與率（{pr['score']}/{pr['max_score']}分）")
    print(f"     模擬：{pr['simulated'] * 100:.1f}%  vs  實際：{pr['actual'] * 100:.1f}%  偏差：{pr['diff'] * 100:.1f}%")

    # 情绪分布
    sd = scoring["details"]["sentiment_distribution"]
    print(f"\n  2️⃣ 情緒分佈（{sd['score']}/{sd['max_score']}分）")
    print(f"     {'':12} 模擬      實際      偏差")
    for key in ["positive", "neutral", "negative"]:
        label = {"positive": "正面", "neutral": "中性", "negative": "負面"}[key]
        print(f"     {label:6}  {sd['simulated'].get(key, 0):6.1f}%  {sd['actual'].get(key, 0):6.1f}%  {sd['diffs'].get(key, 0):6.1f}%")

    # 主导情绪
    ds = scoring["details"]["dominant_sentiment"]
    match_text = "✓ 一致" if ds["match"] else "✗ 不一致"
    print(f"\n  3️⃣ 主導情緒（{ds['score']}/{ds['max_score']}分）")
    print(f"     模擬：{ds['simulated']}  vs  實際：{ds['actual']}  {match_text}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Pionex OASIS 歷史活動回測")
    parser.add_argument("--historical", "--activity", dest="historical", required=True, help="歷史活動數據 JSON 文件路徑")
    parser.add_argument("--personas", default=None, help="用戶畫像 JSON 文件路徑")
    parser.add_argument("--agents", type=int, default=None, help="模擬 Agent 數量")
    args = parser.parse_args()

    # 配置
    model = os.getenv("SIMULATION_MODEL", "gpt-4o-mini")
    agent_count = args.agents or int(os.getenv("AGENT_COUNT", "200"))
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or api_key == "your_key_here":
        print("❌ 請在 .env 中設定有效的 OPENAI_API_KEY")
        sys.exit(1)

    # 加载历史活动数据
    print("📂 載入歷史活動數據...")
    with open(args.historical, "r", encoding="utf-8") as f:
        historical = json.load(f)

    activity_text = build_activity_text(historical)
    actual_results = historical["actual_results"]
    activity_name = historical.get("activity_name", "未命名活動")

    # 生成 Agent 并模拟
    print("👤 載入用戶畫像...")
    personas = load_personas(args.personas)

    print(f"🤖 生成 {agent_count} 個模擬 Agent...")
    agents = generate_agents(personas, agent_count)

    client = OpenAI(api_key=api_key)

    print(f"🚀 開始回測模擬（模型: {model}）...")
    results = []
    for i, agent in enumerate(agents):
        if (i + 1) % 10 == 0 or i == 0:
            print(f"  進度：{i + 1}/{agent_count}")
        result = simulate_agent_response(client, agent, activity_text, model)
        results.append(result)

    # 分析模拟结果
    print("\n📊 分析模擬結果...")
    simulated_analysis = analyze_results(results)

    # 计算方向一致性评分
    scoring = calculate_direction_score(simulated_analysis, actual_results)

    # 打印报告
    print_backtest_report(scoring, activity_name, simulated_analysis)

    # 保存结果
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"backtest_{timestamp}.json"

    output_data = {
        "metadata": {
            "activity_name": activity_name,
            "model": model,
            "agent_count": agent_count,
            "timestamp": timestamp,
        },
        "scoring": scoring,
        "simulated_analysis": simulated_analysis,
        "actual_results": actual_results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"\n💾 結果已保存至：{output_path}")


if __name__ == "__main__":
    main()
