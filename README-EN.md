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

## 🏗️ System Architecture

### Layer Breakdown

| Layer | Core Modules | Responsibilities |
|------|--------------|------------------|
| Presentation | `frontend/src/views/*`, `frontend/src/components/*` | 5-step workflow UI, live simulation status, report and interaction pages |
| API | `backend/app/api/graph.py`, `simulation.py`, `report.py` | Public APIs for graph build, simulation control, report generation and download |
| Orchestration | `simulation_manager.py`, `simulation_runner.py` | Simulation state machine, process lifecycle, pause/resume/stop, live status aggregation |
| Memory & Graph | `graph_builder.py`, `zep_entity_reader.py`, `zep_graph_memory_updater.py` | Seed structuring, graph writing, entity filtering, and post-simulation memory writeback |
| Reasoning & Report | `report_agent.py`, `zep_tools.py`, `utils/llm_client.py` | ReACT multi-step reasoning, tool calls, and interactive prediction report generation |

### Project Code Structure Tree

```text
MiroFish/
├── frontend/                                  # Vue3 frontend project
│   ├── package.json                           # frontend dependencies and scripts
│   ├── vite.config.js                         # Vite build/dev server config
│   ├── index.html                             # frontend HTML entry
│   └── src/
│       ├── main.js                            # Vue app bootstrap
│       ├── App.vue                            # root component
│       ├── api/                               # backend API wrappers
│       │   ├── index.js                       # Axios instance and shared request config
│       │   ├── graph.js                       # graph build related APIs
│       │   ├── simulation.js                  # simulation control APIs
│       │   └── report.js                      # report generation/download/chat APIs
│       ├── router/
│       │   └── index.js                       # frontend routes
│       ├── store/
│       │   └── pendingUpload.js               # pending upload state store
│       ├── views/                             # page-level views
│       │   ├── Home.vue                       # home page
│       │   ├── MainView.vue                   # main workflow container
│       │   ├── Process.vue                    # 5-step process page
│       │   ├── SimulationView.vue             # simulation preparation page
│       │   ├── SimulationRunView.vue          # live simulation monitor page
│       │   ├── ReportView.vue                 # report viewer page
│       │   └── InteractionView.vue            # deep interaction page
│       ├── components/                        # business components
│       │   ├── Step1GraphBuild.vue            # Step1 graph build component
│       │   ├── Step2EnvSetup.vue              # Step2 environment setup component
│       │   ├── Step3Simulation.vue            # Step3 simulation component
│       │   ├── Step4Report.vue                # Step4 report component
│       │   ├── Step5Interaction.vue           # Step5 interaction component
│       │   ├── GraphPanel.vue                 # graph data panel
│       │   └── HistoryDatabase.vue            # historical memory/data panel
│       └── assets/logo/                       # frontend logo assets
│           ├── MiroFish_logo_left.jpeg
│           └── MiroFish_logo_compressed.jpeg
├── backend/                                   # Flask backend project
│   ├── run.py                                 # backend service entrypoint
│   ├── requirements.txt                       # Python dependency list
│   ├── pyproject.toml                         # Python project metadata/tooling
│   ├── uv.lock                                # uv-locked dependency versions
│   ├── app/
│   │   ├── __init__.py                        # Flask app factory and blueprint wiring
│   │   ├── config.py                          # backend config and env loading
│   │   ├── api/                               # API route layer
│   │   │   ├── __init__.py                    # Blueprint initialization
│   │   │   ├── graph.py                       # graph build and graph management endpoints
│   │   │   ├── simulation.py                  # entity read, simulation create/run/control endpoints
│   │   │   └── report.py                      # report generate/query/download/chat endpoints
│   │   ├── services/                          # core business services
│   │   │   ├── graph_builder.py               # GraphRAG graph build service
│   │   │   ├── ontology_generator.py          # ontology/entity type generation
│   │   │   ├── text_processor.py              # seed text cleaning/preprocessing
│   │   │   ├── zep_entity_reader.py           # Zep graph entity read/filter service
│   │   │   ├── oasis_profile_generator.py     # OASIS persona/profile generation
│   │   │   ├── simulation_config_generator.py # simulation config auto-generation
│   │   │   ├── simulation_manager.py          # simulation lifecycle state manager
│   │   │   ├── simulation_runner.py           # background simulation execution/monitoring
│   │   │   ├── simulation_ipc.py              # simulation process IPC protocol
│   │   │   ├── zep_graph_memory_updater.py    # write simulation actions back to graph memory
│   │   │   ├── zep_tools.py                   # ReportAgent tool integrations
│   │   │   └── report_agent.py                # ReACT report generation and Q&A service
│   │   ├── models/                            # state model layer
│   │   │   ├── __init__.py
│   │   │   ├── project.py                     # project state and metadata manager
│   │   │   └── task.py                        # async task state model
│   │   └── utils/                             # shared infrastructure utilities
│   │       ├── __init__.py
│   │       ├── llm_client.py                  # OpenAI-SDK-compatible LLM client
│   │       ├── file_parser.py                 # uploaded file parsing utilities
│   │       ├── logger.py                      # layered logging system
│   │       ├── retry.py                       # retry helpers/decorators
│   │       └── zep_paging.py                  # Zep paging helper
│   ├── scripts/                               # OASIS runtime scripts
│   │   ├── run_parallel_simulation.py         # Twitter + Reddit parallel simulation entry
│   │   ├── run_twitter_simulation.py          # Twitter simulation runner
│   │   ├── run_reddit_simulation.py           # Reddit simulation runner
│   │   ├── action_logger.py                   # agent action logging utility
│   │   └── test_profile_format.py             # profile format validation script
│   ├── uploads/                               # runtime data (projects/simulations/reports)
│   └── logs/                                  # backend runtime logs
├── static/
│   └── image/                                 # README images and demo assets
├── package.json                               # root-level scripts for frontend/backend
├── docker-compose.yml                         # Docker orchestration (frontend + backend)
├── Dockerfile                                 # Docker image build definition
├── .env.example                               # environment variable template
├── README.md                                  # Chinese documentation
├── README-EN.md                               # English documentation
└── LICENSE                                    # open-source license
```

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

The backend supports two LLM providers, switched via `LLM_PROVIDER` (`openai` or `azure_openai`). This feature uses existing dependencies only—**no changes to `pyproject.toml` or `uv.lock` are required**.

```env
# LLM API configuration (any OpenAI-compatible API)
# LLM provider: openai (default) or azure_openai
LLM_PROVIDER=openai

# OpenAI-compatible API (when Provider=openai)
# Recommended: Alibaba Qwen-plus via Bailian: https://bailian.console.aliyun.com/
# High consumption, try simulations with fewer than 40 rounds first
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus

# Zep Cloud configuration
# Azure OpenAI (when Provider=azure_openai)
# Use either AZURE_OPENAI_BASE_URL or AZURE_OPENAI_ENDPOINT
# AZURE_OPENAI_API_KEY=your_azure_key
# AZURE_OPENAI_DEPLOYMENT=your-deployment-name

# Zep Cloud Configuration
# Free monthly quota is sufficient for simple usage: https://app.getzep.com/
ZEP_API_KEY=your_zep_api_key
```

<details>
<summary><b>Using MiniMax Models</b></summary>

[MiniMax](https://platform.minimax.io/) provides high-performance, cost-effective LLM models with OpenAI-compatible API:

```env
LLM_API_KEY=your_minimax_api_key
LLM_BASE_URL=https://api.minimax.io/v1
LLM_MODEL_NAME=MiniMax-M2.5
```

| Model | Description |
|-------|-------------|
| `MiniMax-M2.5` | Flagship model, 204K context window |
| `MiniMax-M2.5-highspeed` | Same performance, faster and more agile |

For users in China: `LLM_BASE_URL=https://api.minimaxi.com/v1`

API Documentation: [OpenAI Compatible API](https://platform.minimax.io/docs/api-reference/text-openai-api)

</details>

#### 2. Install Dependencies
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
