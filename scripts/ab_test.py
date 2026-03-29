"""
Pionex OASIS A/B 推演脚本
并行模拟两套活动方案，输出对比报告。
"""

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# 复用主模拟脚本的核心函数
from run_simulation import (
    ROOT_DIR,
    RESULTS_DIR,
    analyze_results,
    build_activity_text,
    generate_agents,
    load_activity,
    load_personas,
    simulate_agent_response,
)

load_dotenv()


def run_plan_simulation(
    plan_name: str,
    activity: dict,
    agents: list[dict],
    client: OpenAI,
    model: str,
) -> dict:
    """对单个方案运行模拟"""
    activity_text = build_activity_text(activity)
    results = []
    total = len(agents)

    print(f"\n🚀 [{plan_name}] 開始模擬（{total} 個 Agent）...")
    for i, agent in enumerate(agents):
        if (i + 1) % 10 == 0 or i == 0:
            print(f"  [{plan_name}] 進度：{i + 1}/{total}")
        result = simulate_agent_response(client, agent, activity_text, model)
        results.append(result)

    analysis = analyze_results(results)
    return {
        "activity_name": activity.get("activity_name", plan_name),
        "analysis": analysis,
        "raw_results": results,
    }


def print_comparison_report(plan_a_result: dict, plan_b_result: dict):
    """打印 A/B 对比报告"""
    a = plan_a_result["analysis"]
    b = plan_b_result["analysis"]
    a_name = plan_a_result["activity_name"]
    b_name = plan_b_result["activity_name"]

    print("\n" + "=" * 70)
    print("📊 A/B 推演對比報告")
    print("=" * 70)

    # 方案概览
    print(f"\n  方案 A：{a_name}")
    print(f"  方案 B：{b_name}")

    # 参与率对比
    print("\n" + "-" * 70)
    print("📈 參與率對比")
    print("-" * 70)
    a_rate = a["participation_rate"] * 100
    b_rate = b["participation_rate"] * 100
    winner_rate = "A" if a_rate > b_rate else "B" if b_rate > a_rate else "平手"
    print(f"  方案 A：{a_rate:.1f}%")
    print(f"  方案 B：{b_rate:.1f}%")
    print(f"  差距：{abs(a_rate - b_rate):.1f}%")
    print(f"  🏆 勝出：方案 {winner_rate}")

    # 情绪分布对比
    print("\n" + "-" * 70)
    print("🎭 情緒分佈對比")
    print("-" * 70)
    print(f"  {'':12} {'方案 A':>10} {'方案 B':>10} {'差異':>10}")
    for key in ["positive", "neutral", "negative"]:
        label = {"positive": "正面", "neutral": "中性", "negative": "負面"}[key]
        a_val = a["sentiment_percentages"].get(key, 0)
        b_val = b["sentiment_percentages"].get(key, 0)
        diff = a_val - b_val
        sign = "+" if diff > 0 else ""
        print(f"  {label:8} {a_val:9.1f}% {b_val:9.1f}% {sign}{diff:9.1f}%")

    # 负面反馈对比
    print("\n" + "-" * 70)
    print("⚠️ 負面反饋對比")
    print("-" * 70)
    a_neg = a["sentiment_percentages"].get("negative", 0)
    b_neg = b["sentiment_percentages"].get("negative", 0)
    lower_neg = "A" if a_neg < b_neg else "B" if b_neg < a_neg else "相同"
    print(f"  負面比例較低的方案：{lower_neg}")

    print(f"\n  [方案 A] 典型負面反饋：")
    for i, c in enumerate(a.get("negative_feedback_samples", [])[:3], 1):
        display = c[:70] + "..." if len(c) > 70 else c
        print(f"    {i}. {display}")

    print(f"\n  [方案 B] 典型負面反饋：")
    for i, c in enumerate(b.get("negative_feedback_samples", [])[:3], 1):
        display = c[:70] + "..." if len(c) > 70 else c
        print(f"    {i}. {display}")

    # 各画像类型对比
    print("\n" + "-" * 70)
    print("👤 各畫像類型參與率對比")
    print("-" * 70)
    all_types = set(list(a["persona_breakdown"].keys()) + list(b["persona_breakdown"].keys()))
    for ptype in sorted(all_types):
        a_stat = a["persona_breakdown"].get(ptype, {})
        b_stat = b["persona_breakdown"].get(ptype, {})
        a_pr = a_stat.get("participation_rate", 0) * 100
        b_pr = b_stat.get("participation_rate", 0) * 100
        better = "A" if a_pr > b_pr else "B" if b_pr > a_pr else "="
        print(f"  {ptype:12}  A: {a_pr:5.1f}%  B: {b_pr:5.1f}%  → {better}")

    # 总结建议
    print("\n" + "=" * 70)
    print("💡 總結建議")
    print("=" * 70)

    if a_rate > b_rate and a_neg <= b_neg:
        print("  ✅ 建議採用方案 A（參與率更高且負面反饋不多於方案 B）")
    elif b_rate > a_rate and b_neg <= a_neg:
        print("  ✅ 建議採用方案 B（參與率更高且負面反饋不多於方案 A）")
    elif a_rate > b_rate and a_neg > b_neg:
        print("  ⚠️ 方案 A 參與率較高，但負面反饋也較多。建議根據業務優先級決定。")
    elif b_rate > a_rate and b_neg > a_neg:
        print("  ⚠️ 方案 B 參與率較高，但負面反饋也較多。建議根據業務優先級決定。")
    else:
        print("  🤔 兩方案表現接近，建議結合其他因素（成本、品牌形象等）綜合考量。")

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Pionex OASIS A/B 活動推演")
    parser.add_argument("--plan-a", required=True, help="方案 A 活動數據 JSON 文件路徑")
    parser.add_argument("--plan-b", required=True, help="方案 B 活動數據 JSON 文件路徑")
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

    # 加载数据
    print("📂 載入活動方案...")
    activity_a = load_activity(args.plan_a)
    activity_b = load_activity(args.plan_b)

    print("👤 載入用戶畫像...")
    personas = load_personas(args.personas)

    # 两个方案使用相同的 Agent 组合（确保公平对比）
    print(f"🤖 生成 {agent_count} 個模擬 Agent...")
    agents = generate_agents(personas, agent_count)

    client = OpenAI(api_key=api_key)

    # 依次运行两个方案的模拟
    plan_a_result = run_plan_simulation("方案A", activity_a, agents, client, model)
    plan_b_result = run_plan_simulation("方案B", activity_b, agents, client, model)

    # 打印对比报告
    print_comparison_report(plan_a_result, plan_b_result)

    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"ab_test_{timestamp}.json"

    output_data = {
        "metadata": {
            "model": model,
            "agent_count": agent_count,
            "timestamp": timestamp,
        },
        "plan_a": {
            "activity_name": plan_a_result["activity_name"],
            "analysis": plan_a_result["analysis"],
        },
        "plan_b": {
            "activity_name": plan_b_result["activity_name"],
            "analysis": plan_b_result["analysis"],
        },
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"\n💾 結果已保存至：{output_path}")


if __name__ == "__main__":
    main()
