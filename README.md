# Pionex OASIS POC

利用 [OASIS](https://github.com/camel-ai/oasis)（Open Agent Social Interaction Simulations）模拟引擎，对 Pionex 加密交易平台的运营活动进行预发布推演，在活动正式投放前预判参与率、情绪分布和典型负面反馈。

## 项目简介

OASIS 是由 CAMEL-AI 开发的多智能体社交模拟框架。本项目将其应用于加密交易平台的运营场景，通过构建具备真实用户画像的 AI Agent 群体，模拟不同类型用户对活动方案的真实反应，输出可量化的预测指标（参与率、情绪分布）并与历史真实数据对比校验。

本 POC 覆盖两个阶段：
- **Phase 0**：历史活动回测验证，证明模拟引擎的预测精度达到实用门槛
- **Phase 1**：新活动 A/B 方案推演，为运营决策提供数据依据

## 环境要求

- Python 3.10+
- `camel-oasis` 库及依赖（见 `requirements.txt`）
- OpenAI API Key（用于驱动 Agent 推理，默认模型 `gpt-4o-mini`）

## 安装

```bash
# 克隆项目
git clone <repo-url>
cd pionex-oasis-poc

# 安装依赖
pip install -r requirements.txt
```

## 配置

复制示例文件并填写 API Key：

```bash
cp .env.example .env
```

编辑 `.env`：

```dotenv
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

> `.env` 已添加至 `.gitignore`，不会提交到代码仓库。

## 使用指南

### 1. 跑模拟（单方案推演）

对单个活动方案进行全量模拟，输出情绪分布、参与率和典型评论样本。

```bash
python3 scripts/run_simulation.py
```

默认读取 `data/sample_activity.json`，结果写入 `results/simulation_YYYYMMDD_HHMMSS.json`。

### 2. 跑回测（历史活动校验）

将模拟结果与历史真实数据进行对比，输出方向一致性评分。评分 ≥70 判定为 **GO**，否则为 **NO-GO**。

```bash
python3 scripts/backtest.py
```

默认读取 `data/historical_applepay_activity.json` 作为待测活动、内置真实数据作为对照。结果写入 `results/backtest_YYYYMMDD_HHMMSS.json`。

### 3. 跑推演（A/B 方案对比）

并行模拟两套活动方案，输出对比分析报告，支持参与率、情绪分布和画像细分对比。

```bash
python3 scripts/ab_test.py
```

默认读取 `data/ab_test_variant_a.json` 和 `data/ab_test_variant_b.json`。结果写入 `results/ab_test_YYYYMMDD_HHMMSS.json`。

## 目录结构

```
pionex-oasis-poc/
├── personas/
│   └── pionex_personas.json        # 6 类用户 Agent 画像（含繁体中文评论模板）
├── scripts/
│   ├── run_simulation.py           # 单方案模拟脚本
│   ├── backtest.py                 # 历史回测脚本
│   └── ab_test.py                  # A/B 推演脚本
├── data/
│   ├── sample_activity.json        # 示例活动配置
│   ├── sample_historical.json      # 示例历史数据
│   ├── historical_applepay_activity.json  # Apple Pay 活动配置（Phase 0 回测用）
│   ├── ab_test_variant_a.json      # A/B 推演：方案 A（手续费返还）
│   └── ab_test_variant_b.json      # A/B 推演：方案 B（排行榜挑战赛）
├── results/                        # 模拟输出目录（自动生成，已 gitignore 原始结果）
├── requirements.txt
├── .env.example
├── .env                            # 本地密钥配置（不提交）
├── README.md
└── PROJECT_REPORT.md               # 项目结项报告
```

## 输出说明

所有结果以 JSON 格式保存在 `results/` 目录，包含：

- `metadata`：模型、Agent 数量、时间戳
- `scoring`：总分、分项得分、GO/NO-GO 判定（回测专属）
- `simulated_analysis`：参与率、情绪分布、画像细分、评论样本
- `actual_results`：历史真实数据（回测专属）

回测评分规则：
| 维度 | 满分 | 通过阈值 |
|------|------|---------|
| 参与率误差 | 40 | 差值 ≤5% |
| 情绪分布平均误差 | 40 | 平均差 ≤10% |
| 主导情绪一致性 | 20 | 方向一致 |
| **合计** | **100** | **≥70 → GO** |
