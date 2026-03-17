<div align="center">

<img src="./static/image/MiroFish_logo_compressed.jpeg" alt="MiroFish Logo" width="75%"/>

<a href="https://trendshift.io/repositories/16144" target="_blank"><img src="https://trendshift.io/api/badge/repositories/16144" alt="666ghj%2FMiroFish | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

A Simple and Universal Swarm Intelligence Engine, Predicting Anything
</br>
<em>A Simple and Universal Swarm Intelligence Engine, Predicting Anything</em>

<a href="https://www.shanda.com/" target="_blank"><img src="./static/image/shanda_logo.png" alt="666ghj%2FMiroFish | Shanda" height="40"/></a>

[![GitHub Stars](https://img.shields.io/github/stars/666ghj/MiroFish?style=flat-square&color=DAA520)](https://github.com/666ghj/MiroFish/stargazers)
[![GitHub Watchers](https://img.shields.io/github/watchers/666ghj/MiroFish?style=flat-square)](https://github.com/666ghj/MiroFish/watchers)
[![GitHub Forks](https://img.shields.io/github/forks/666ghj/MiroFish?style=flat-square)](https://github.com/666ghj/MiroFish/network)
[![Docker](https://img.shields.io/badge/Docker-Build-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/666ghj/MiroFish)

[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discord.com/channels/1469200078932545606/1469201282077163739)
[![X](https://img.shields.io/badge/X-Follow-000000?style=flat-square&logo=x&logoColor=white)](https://x.com/mirofish_ai)
[![Instagram](https://img.shields.io/badge/Instagram-Follow-E4405F?style=flat-square&logo=instagram&logoColor=white)](https://www.instagram.com/mirofish_ai/)

[README](./README.md) | [Alternate Copy](./README-EN.md)
[English](./README-EN.md) | [中文文档](./README.md) | [한국어](./README-KO.md)

</div>

## ⚡ Overview

**MiroFish** is a next-generation AI prediction engine powered by multi-agent technology. By extracting seed information from the real world such as breaking news, policy drafts, or financial signals, it automatically constructs a high-fidelity parallel digital world. Within this space, thousands of intelligent agents with independent personalities, long-term memory, and behavioral logic freely interact and undergo social evolution. You can inject variables dynamically from a God's-eye view to infer future trajectories with much higher context.

> You only need to upload seed materials such as reports or stories and describe your prediction request in natural language.</br>
> MiroFish returns a detailed prediction report and a deeply interactive high-fidelity digital world.

### Vision

MiroFish aims to build a swarm-intelligence mirror of reality by modeling emergent collective behavior from individual interactions:

- **Macro use cases**: a rehearsal lab for decision-makers to test policy or communications strategies with near-zero real-world risk.
- **Micro use cases**: a creative sandbox for individuals to explore novel endings, alternate histories, or speculative scenarios.

From serious forecasting to playful simulation, MiroFish is designed to make "what if" questions explorable.

## 🌐 Live Demo

Try the online demo here: [mirofish-live-demo](https://666ghj.github.io/mirofish-demo/)

## 📸 Screenshots

<div align="center">
<table>
<tr>
<td><img src="./static/image/Screenshot/运行截图1.png" alt="Screenshot 1" width="100%"/></td>
<td><img src="./static/image/Screenshot/运行截图2.png" alt="Screenshot 2" width="100%"/></td>
</tr>
<tr>
<td><img src="./static/image/Screenshot/运行截图3.png" alt="Screenshot 3" width="100%"/></td>
<td><img src="./static/image/Screenshot/运行截图4.png" alt="Screenshot 4" width="100%"/></td>
</tr>
<tr>
<td><img src="./static/image/Screenshot/运行截图5.png" alt="Screenshot 5" width="100%"/></td>
<td><img src="./static/image/Screenshot/运行截图6.png" alt="Screenshot 6" width="100%"/></td>
</tr>
</table>
</div>

## 🎬 Demo Videos

### 1. Wuhan University Public Opinion Simulation + MiroFish Introduction

<div align="center">
<a href="https://www.bilibili.com/video/BV1VYBsBHEMY/" target="_blank"><img src="./static/image/武大模拟演示封面.png" alt="MiroFish Demo Video" width="75%"/></a>

Click the image to watch the full demo video based on a BettaFish-generated Wuhan University public-opinion report.
</div>

### 2. Dream of the Red Chamber Lost Ending Simulation

<div align="center">
<a href="https://www.bilibili.com/video/BV1cPk3BBExq" target="_blank"><img src="./static/image/红楼梦模拟推演封面.jpg" alt="MiroFish Demo Video" width="75%"/></a>

Click the image to watch MiroFish infer a lost ending based on the first 80 chapters of *Dream of the Red Chamber*.
</div>

> More examples for finance, politics, and current-events forecasting are planned.

## 🔄 Workflow

1. **Graph Building**: extract seeds from source material, inject individual and collective memory, and build a GraphRAG-ready graph.
2. **Environment Setup**: extract entities and relationships, generate personas, and inject simulation parameters.
3. **Simulation**: run dual-platform simulations, parse the prediction request, and update temporal memory dynamically.
4. **Report Generation**: use ReportAgent and its tools to analyze the post-simulation environment.
5. **Deep Interaction**: talk to agents inside the simulated world or continue through ReportAgent.

## 🏗️ 系统架构

### 分层说明

| 层级 | 核心模块 | 职责 |
|------|----------|------|
| 表现层 | `frontend/src/views/*`、`frontend/src/components/*` | 五步流程 UI、实时模拟状态展示、报告与深度交互页面 |
| API 层 | `backend/app/api/graph.py`、`simulation.py`、`report.py` | 对外提供图谱构建、模拟控制、报告生成与下载接口 |
| 编排层 | `simulation_manager.py`、`simulation_runner.py` | 模拟状态机、进程管理、暂停/恢复/停止与实时状态汇总 |
| 记忆与图谱层 | `graph_builder.py`、`zep_entity_reader.py`、`zep_graph_memory_updater.py` | 种子数据结构化、图谱写入、实体过滤与模拟后记忆回灌 |
| 推理与报告层 | `report_agent.py`、`zep_tools.py`、`utils/llm_client.py` | ReACT 多轮推理、工具调用、自动生成可交互预测报告 |

### 项目代码结构树

```text
MiroFish/
├── frontend/                                  # Vue3 前端工程
│   ├── package.json                           # 前端依赖与脚本定义
│   ├── vite.config.js                         # Vite 构建与开发服务配置
│   ├── index.html                             # 前端入口 HTML 模板
│   └── src/
│       ├── main.js                            # Vue 应用启动入口
│       ├── App.vue                            # 根组件
│       ├── api/                               # 后端接口封装层
│       │   ├── index.js                       # Axios 实例与统一请求配置
│       │   ├── graph.js                       # 图谱构建相关 API
│       │   ├── simulation.js                  # 模拟流程控制 API
│       │   └── report.js                      # 报告生成/下载/对话 API
│       ├── router/
│       │   └── index.js                       # 前端路由配置
│       ├── store/
│       │   └── pendingUpload.js               # 待上传文件状态管理
│       ├── views/                             # 页面级视图
│       │   ├── Home.vue                       # 首页（项目介绍与入口）
│       │   ├── MainView.vue                   # 主流程容器页
│       │   ├── Process.vue                    # 五步流程总览页
│       │   ├── SimulationView.vue             # 模拟准备页
│       │   ├── SimulationRunView.vue          # 模拟运行监控页
│       │   ├── ReportView.vue                 # 报告查看页
│       │   └── InteractionView.vue            # 深度交互页
│       ├── components/                        # 业务组件
│       │   ├── Step1GraphBuild.vue            # Step1 图谱构建组件
│       │   ├── Step2EnvSetup.vue              # Step2 环境搭建组件
│       │   ├── Step3Simulation.vue            # Step3 模拟控制组件
│       │   ├── Step4Report.vue                # Step4 报告生成组件
│       │   ├── Step5Interaction.vue           # Step5 深度交互组件
│       │   ├── GraphPanel.vue                 # 图谱数据展示面板
│       │   └── HistoryDatabase.vue            # 历史数据/记忆展示组件
│       └── assets/logo/                       # 前端 Logo 资源
│           ├── MiroFish_logo_left.jpeg
│           └── MiroFish_logo_compressed.jpeg
├── backend/                                   # Flask 后端工程
│   ├── run.py                                 # 后端服务启动入口
│   ├── requirements.txt                       # Python 依赖清单
│   ├── pyproject.toml                         # Python 项目元数据与工具配置
│   ├── uv.lock                                # uv 锁定依赖版本
│   ├── app/
│   │   ├── __init__.py                        # Flask 应用工厂与蓝图注册
│   │   ├── config.py                          # 后端配置与环境变量读取
│   │   ├── api/                               # API 路由层
│   │   │   ├── __init__.py                    # Blueprint 初始化
│   │   │   ├── graph.py                       # 图谱构建与图谱管理接口
│   │   │   ├── simulation.py                  # 实体读取、模拟创建/运行/控制接口
│   │   │   └── report.py                      # 报告生成、查询、下载与问答接口
│   │   ├── services/                          # 核心业务服务层
│   │   │   ├── graph_builder.py               # GraphRAG 图谱构建服务
│   │   │   ├── ontology_generator.py          # 本体/实体类型生成服务
│   │   │   ├── text_processor.py              # 种子文本清洗与预处理
│   │   │   ├── zep_entity_reader.py           # Zep 图谱实体读取与过滤
│   │   │   ├── oasis_profile_generator.py     # OASIS 角色画像生成
│   │   │   ├── simulation_config_generator.py # 模拟配置自动生成
│   │   │   ├── simulation_manager.py          # 模拟状态机与生命周期管理
│   │   │   ├── simulation_runner.py           # 后台模拟进程执行与监控
│   │   │   ├── simulation_ipc.py              # 模拟进程 IPC 通信协议
│   │   │   ├── zep_graph_memory_updater.py    # 模拟动作回写图谱记忆
│   │   │   ├── zep_tools.py                   # ReportAgent 可调用的检索工具集
│   │   │   └── report_agent.py                # ReACT 报告生成与交互问答
│   │   ├── models/                            # 状态模型层
│   │   │   ├── __init__.py
│   │   │   ├── project.py                     # 项目状态与元数据管理
│   │   │   └── task.py                        # 异步任务状态模型
│   │   └── utils/                             # 通用基础设施
│   │       ├── __init__.py
│   │       ├── llm_client.py                  # OpenAI SDK 兼容 LLM 客户端
│   │       ├── file_parser.py                 # 上传文件解析与抽取工具
│   │       ├── logger.py                      # 分层日志系统
│   │       ├── retry.py                       # 通用重试装饰器/逻辑
│   │       └── zep_paging.py                  # Zep 分页读取工具
│   ├── scripts/                               # OASIS 执行脚本
│   │   ├── run_parallel_simulation.py         # Twitter + Reddit 并行模拟入口
│   │   ├── run_twitter_simulation.py          # Twitter 模拟执行脚本
│   │   ├── run_reddit_simulation.py           # Reddit 模拟执行脚本
│   │   ├── action_logger.py                   # Agent 行为日志采集脚本
│   │   └── test_profile_format.py             # 画像格式校验脚本
│   ├── uploads/                               # 运行时数据目录（项目/模拟/报告产物）
│   └── logs/                                  # 后端日志输出目录
├── static/
│   └── image/                                 # README 图片与演示资源
├── package.json                               # 根目录脚本（联动前后端）
├── docker-compose.yml                         # Docker 编排（前端+后端）
├── Dockerfile                                 # Docker 镜像构建定义
├── .env.example                               # 环境变量示例
├── README.md                                  # 中文文档
├── README-EN.md                               # 英文文档
└── LICENSE                                    # 开源许可证
```

## 🚀 快速开始
## 🚀 Quick Start

### Option 1: Run From Source

#### Prerequisites

| Tool | Version | Description | Check |
|------|---------|-------------|-------|
| **Node.js** | 18+ | Frontend runtime, includes npm | `node -v` |
| **Python** | >=3.11, <=3.12 | Backend runtime | `python --version` |
| **uv** | Latest | Python package manager | `uv --version` |

#### 1. Configure environment variables

```bash
cp .env.example .env
```

Fill in the required API keys in `.env`.

后端支持两种 LLM 提供商，通过 `LLM_PROVIDER` 切换（`openai` 或 `azure_openai`）。本功能仅使用现有依赖，**无需修改 `pyproject.toml` 或 `uv.lock`**。

```env
# LLM API configuration (any OpenAI-compatible API)
# LLM 提供商：openai（默认）或 azure_openai
LLM_PROVIDER=openai

# OpenAI 兼容 API（Provider=openai 时使用）
# 推荐使用阿里百炼平台 qwen-plus：https://bailian.console.aliyun.com/
# 注意消耗较大，可先进行小于40轮的模拟尝试
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus

# Zep Cloud configuration
# Azure OpenAI（Provider=azure_openai 时使用）
# 二选一：AZURE_OPENAI_BASE_URL 或 AZURE_OPENAI_ENDPOINT
# AZURE_OPENAI_API_KEY=your_azure_key
# AZURE_OPENAI_DEPLOYMENT=your-deployment-name

# Zep Cloud 配置
# 每月免费额度即可支撑简单使用：https://app.getzep.com/
ZEP_API_KEY=your_zep_api_key
```

<details>
<summary><b>使用 MiniMax 模型</b></summary>

[MiniMax](https://platform.minimax.io/) 提供高性能、高性价比的 LLM 模型，支持 OpenAI 兼容 API：

```env
LLM_API_KEY=your_minimax_api_key
LLM_BASE_URL=https://api.minimax.io/v1
LLM_MODEL_NAME=MiniMax-M2.5
```

| 模型 | 说明 |
|------|------|
| `MiniMax-M2.5` | 旗舰模型，204K 上下文窗口 |
| `MiniMax-M2.5-highspeed` | 同等性能，更快更敏捷 |

国内用户可使用：`LLM_BASE_URL=https://api.minimaxi.com/v1`

API 文档：[OpenAI 兼容接口](https://platform.minimax.io/docs/api-reference/text-openai-api)

</details>

#### 2. 安装依赖
#### 2. Install dependencies

```bash
npm run setup:all
```

Or install by layer:

```bash
npm run setup
npm run setup:backend
```

#### 3. Start services

```bash
npm run dev
```

Service URLs:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:5001`

Run individually:

```bash
npm run backend
npm run frontend
```

### Option 2: Docker

```bash
cp .env.example .env
docker compose up -d
```

This reads the root `.env` file and maps ports `3000` and `5001`.

## 📬 Contact

<div align="center">
<img src="./static/image/QQ群.png" alt="Community Group QR Code" width="60%"/>
</div>

The MiroFish team is recruiting full-time and internship roles. Contact: **mirofish@shanda.com**

## 📄 Acknowledgments

**MiroFish has received strategic support and incubation from Shanda Group.**

MiroFish's simulation engine is powered by **[OASIS](https://github.com/camel-ai/oasis)**. Thanks to the CAMEL-AI team for the open-source foundation.

## 📈 Project Statistics

<a href="https://www.star-history.com/#666ghj/MiroFish&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=666ghj/MiroFish&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=666ghj/MiroFish&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=666ghj/MiroFish&type=date&legend=top-left" />
 </picture>
</a>
