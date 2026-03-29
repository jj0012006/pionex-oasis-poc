"""
Pionex OASIS 模拟主脚本
模拟 Pionex 用户对运营活动的反应，输出情绪分布、参与率和典型评论。
"""

import argparse
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def load_personas(personas_path: str = None) -> list[dict]:
    """从 JSON 文件加载用户画像"""
    if personas_path is None:
        personas_path = ROOT_DIR / "personas" / "pionex_personas.json"
    with open(personas_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_activity(activity_path: str) -> dict:
    """加载活动数据"""
    with open(activity_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_agents(personas: list[dict], total_count: int) -> list[dict]:
    """按比例生成 Agent 列表"""
    agents = []
    for persona in personas:
        count = round(total_count * persona["ratio"])
        age_low, age_high = map(int, persona["age_range"].split("-"))
        for _ in range(count):
            agent = {
                "persona_type": persona["persona_type"],
                "age": random.randint(age_low, age_high),
                "traits": persona["traits"],
                "trading_style": persona["trading_style"],
                "prompt_template": persona["prompt_template"],
                "reaction_to_bonus_events": persona["reaction_to_bonus_events"],
            }
            agents.append(agent)

    # 补齐或裁剪到目标数量
    while len(agents) < total_count:
        agents.append(random.choice(agents).copy())
    agents = agents[:total_count]
    random.shuffle(agents)
    return agents


def build_activity_text(activity: dict) -> str:
    """将活动数据组装为描述文本"""
    rules_text = "\n".join(f"  - {r}" for r in activity.get("activity_rules", []))
    return f"""{activity['activity_description']}

📋 活動規則：
{rules_text}"""


def simulate_agent_response(client: OpenAI, agent: dict, activity_text: str, model: str) -> dict:
    """模拟单个 Agent 对活动的反应"""
    # 填充 prompt 模板
    prompt = agent["prompt_template"].format(
        age=agent["age"],
        activity_description=activity_text,
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一個台灣加密貨幣社群中的真實用戶。你正在看到 Pionex 派網推出的一個真實活動"
                        "——派卡 + Apple Pay 整合，**首刷完全免費，最高返 6 USDT 現金**（零門檻、零風險的真實現金福利）。\n\n"
                        "【重要背景】這是一個真實的高福利營銷活動：\n"
                        "- 不是抽獎，是確定能拿到的現金\n"
                        "- 新用戶首刷完全免費\n"
                        "- 只需要綁一下 Apple Pay，門檻極低\n"
                        "- 對台灣用戶來說這個力度蠻大的\n\n"
                        "請根據你的人設直實反應——你的個性、習慣和今天的狀態決定你的情緒。\n"
                        "用口語化的繁體中文，像在 LINE 群組或 Telegram 社群聊天一樣自然簡短。\n\n"
                        "【關鍵指引】:\n"
                        "大多數時候，看到這類「確定的免費福利」，你的直覺反應應該是**正面的**——\n"
                        "即使你最後不會真的去參與（因為懶、忙、沒興趣交易等），\n"
                        "但**看到這個活動時，你的情緒應該是「嗯不錯」、「有點香」或至少「還不錯」**。\n\n"
                        "情緒分布指南（基於真實心理）：\n"
                        "- 💚 **正面（約 60-70% 機率）**：你注意到這個活動，直覺反應是「免費的？還不錯」「有誠意」「香啦」\n"
                        "- 😐 **中性（約 20-30% 機率）**：你今天太忙（盯盤、工作、玩遊戲），根本沒心思看，一眼掃過\n"
                        "- ❌ **負面（約 5-10% 機率）**：只有懷疑論者或對平台有顧慮的人才會質疑\n\n"
                        "回覆格式（必須照此格式）：\n"
                        "行動：[留言/點讚/忽略/分享]\n"
                        "情緒：[正面/中性/負面]\n"
                        "是否參與：[是/否/考慮中]\n"
                        "評論內容：[你的評論，若選擇忽略則寫「略過」]"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.9,
            max_tokens=300,
        )
        reply = response.choices[0].message.content.strip()
        return parse_agent_reply(reply, agent)
    except Exception as e:
        print(f"  ⚠ Agent 回應失敗 ({agent['persona_type']}): {e}")
        return {
            "persona_type": agent["persona_type"],
            "action": "error",
            "sentiment": "neutral",
            "will_participate": "否",
            "comment": f"[錯誤: {e}]",
        }


def parse_agent_reply(reply: str, agent: dict) -> dict:
    """解析 Agent 的回覆，提取结构化信息"""
    result = {
        "persona_type": agent["persona_type"],
        "age": agent["age"],
        "action": "留言",
        "sentiment": "中性",
        "will_participate": "考慮中",
        "comment": reply,
        "raw_reply": reply,
    }

    # 逐行解析
    for line in reply.split("\n"):
        line = line.strip()
        if line.startswith("行動：") or line.startswith("行動:"):
            result["action"] = line.split("：" if "：" in line else ":")[1].strip()
        elif line.startswith("情緒：") or line.startswith("情緒:"):
            result["sentiment"] = line.split("：" if "：" in line else ":")[1].strip()
        elif line.startswith("是否參與：") or line.startswith("是否參與:"):
            result["will_participate"] = line.split("：" if "：" in line else ":")[1].strip()
        elif line.startswith("評論內容：") or line.startswith("評論內容:"):
            result["comment"] = line.split("：" if "：" in line else ":")[1].strip()

    return result


def classify_sentiment(sentiment_text: str) -> str:
    """将情绪文本归类为 positive/neutral/negative"""
    if any(w in sentiment_text for w in ["正面", "正向", "積極", "開心", "期待"]):
        return "positive"
    elif any(w in sentiment_text for w in ["負面", "負向", "消極", "失望", "懷疑", "不滿"]):
        return "negative"
    return "neutral"


def analyze_results(results: list[dict]) -> dict:
    """分析模拟结果，生成统计报告"""
    df = pd.DataFrame(results)
    total = len(df)

    # 情绪分布
    df["sentiment_class"] = df["sentiment"].apply(classify_sentiment)
    sentiment_counts = df["sentiment_class"].value_counts()
    sentiment_dist = {
        "positive": int(sentiment_counts.get("positive", 0)),
        "neutral": int(sentiment_counts.get("neutral", 0)),
        "negative": int(sentiment_counts.get("negative", 0)),
    }

    # 参与率
    participate_yes = df["will_participate"].apply(
        lambda x: any(w in str(x) for w in ["是", "會", "要", "參加"])
    ).sum()
    participation_rate = participate_yes / total if total > 0 else 0

    # 按画像类型统计
    persona_stats = {}
    for ptype, group in df.groupby("persona_type"):
        group_sentiment = group["sentiment_class"].value_counts()
        group_participate = group["will_participate"].apply(
            lambda x: any(w in str(x) for w in ["是", "會", "要", "參加"])
        ).sum()
        persona_stats[ptype] = {
            "count": len(group),
            "participation_rate": round(group_participate / len(group), 3),
            "sentiment": {
                "positive": int(group_sentiment.get("positive", 0)),
                "neutral": int(group_sentiment.get("neutral", 0)),
                "negative": int(group_sentiment.get("negative", 0)),
            },
        }

    # 典型评论样本（排除忽略和错误）
    valid_comments = df[
        (~df["comment"].isin(["略過", "[錯誤]"]))
        & (df["action"] != "error")
        & (df["comment"].str.len() > 5)
    ]
    sample_comments = valid_comments.sample(min(10, len(valid_comments)))["comment"].tolist()

    # 负面评论样本
    negative_comments = df[df["sentiment_class"] == "negative"]
    negative_samples = negative_comments.sample(min(5, len(negative_comments)))["comment"].tolist()

    return {
        "total_agents": total,
        "participation_rate": round(participation_rate, 3),
        "sentiment_distribution": sentiment_dist,
        "sentiment_percentages": {
            k: round(v / total * 100, 1) for k, v in sentiment_dist.items()
        },
        "persona_breakdown": persona_stats,
        "sample_comments": sample_comments,
        "negative_feedback_samples": negative_samples,
    }


def print_report(analysis: dict, activity_name: str):
    """在终端打印模拟报告"""
    print("\n" + "=" * 60)
    print(f"📊 模擬報告：{activity_name}")
    print("=" * 60)

    print(f"\n👥 模擬 Agent 數量：{analysis['total_agents']}")
    print(f"📈 預估參與率：{analysis['participation_rate'] * 100:.1f}%")

    print("\n🎭 情緒分佈：")
    sp = analysis["sentiment_percentages"]
    print(f"  ✅ 正面：{sp['positive']}%")
    print(f"  😐 中性：{sp['neutral']}%")
    print(f"  ❌ 負面：{sp['negative']}%")

    print("\n👤 各畫像類型統計：")
    for ptype, stats in analysis["persona_breakdown"].items():
        print(f"  [{ptype}] 人數: {stats['count']}, 參與率: {stats['participation_rate'] * 100:.1f}%")

    print("\n💬 典型評論樣本：")
    for i, comment in enumerate(analysis["sample_comments"], 1):
        # 截取前 80 字符显示
        display = comment[:80] + "..." if len(comment) > 80 else comment
        print(f"  {i}. {display}")

    if analysis["negative_feedback_samples"]:
        print("\n⚠️ 負面反饋樣本：")
        for i, comment in enumerate(analysis["negative_feedback_samples"], 1):
            display = comment[:80] + "..." if len(comment) > 80 else comment
            print(f"  {i}. {display}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Pionex OASIS 活動模擬")
    parser.add_argument("--activity", required=True, help="活動數據 JSON 文件路徑")
    parser.add_argument("--personas", default=None, help="用戶畫像 JSON 文件路徑")
    parser.add_argument("--agents", type=int, default=None, help="模擬 Agent 數量（覆蓋 .env 設定）")
    parser.add_argument("--output", default=None, help="結果輸出文件路徑")
    args = parser.parse_args()

    # 配置
    model = os.getenv("SIMULATION_MODEL", "gpt-4o-mini")
    agent_count = args.agents or int(os.getenv("AGENT_COUNT", "200"))
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or api_key == "your_key_here":
        print("❌ 請在 .env 中設定有效的 OPENAI_API_KEY")
        sys.exit(1)

    # 加载数据
    print("📂 載入活動數據...")
    activity = load_activity(args.activity)
    activity_text = build_activity_text(activity)

    print("👤 載入用戶畫像...")
    personas = load_personas(args.personas)

    print(f"🤖 生成 {agent_count} 個模擬 Agent...")
    agents = generate_agents(personas, agent_count)

    # 初始化 OpenAI 客户端
    client = OpenAI(api_key=api_key)

    # 运行模拟
    print(f"🚀 開始模擬（模型: {model}）...")
    results = []
    for i, agent in enumerate(agents):
        if (i + 1) % 10 == 0 or i == 0:
            print(f"  進度：{i + 1}/{agent_count}")
        result = simulate_agent_response(client, agent, activity_text, model)
        results.append(result)

    # 分析结果
    print("\n📊 分析結果...")
    analysis = analyze_results(results)

    # 打印报告
    print_report(analysis, activity.get("activity_name", "未命名活動"))

    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = args.output or str(RESULTS_DIR / f"simulation_{timestamp}.json")

    output_data = {
        "metadata": {
            "activity_name": activity.get("activity_name"),
            "model": model,
            "agent_count": agent_count,
            "timestamp": timestamp,
        },
        "analysis": analysis,
        "raw_results": results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"\n💾 結果已保存至：{output_path}")


if __name__ == "__main__":
    main()
