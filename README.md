# Academic Paper Assistant · 学术论文助手 v2

> 从选题、检索真实文献到生成可编辑、可导出的学术论文初稿 —— 一个自托管的全栈系统。
> From research question to a complete, editable and exportable manuscript — self-hosted.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.11x-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 1. 系统能力 | What it does

| 能力 | 说明 |
|---|---|
| 真实文献检索 | 并发查询 OpenAlex、Crossref、arXiv（可选 Semantic Scholar），合并去重、按相关度排序，并缓存 72 小时 |
| 分阶段生成 | 检索 → 提纲 → 逐节写作 → 摘要 → 参考文献，每一步的状态、耗时、字数都写入数据库并通过 SSE 实时推送 |
| 可编辑稿件 | 任意章节可在线编辑、可带着补充要求单独重写，其余章节内容作为上下文保证前后一致 |
| 引用规范 | APA 7、MLA 9、IEEE、GB/T 7714-2015 四种参考文献格式，正文引用编号与文献表一一对应 |
| 多格式导出 | Word（.docx，中文宋体/黑体排版）、PDF（中文字体嵌入）、Markdown、BibTeX |
| 账户体系 | 邮箱 + 密码注册登录，JWT 鉴权，论文按用户隔离，管理员账号首次启动自动创建 |
| 过程留痕 | 每次生成/编辑都写事件日志，前端可查看「过程日志」，便于复核与学术诚信披露 |
| 自托管 | 单进程同时提供 API 与前端静态资源，一条 systemd 服务即可上线 |

### 技术栈

- **后端**：FastAPI + Uvicorn + SQLite（WAL）+ httpx
- **前端**：React 18 + TypeScript + Vite + Tailwind CSS
- **模型**：任意 OpenAI 兼容接口（DeepSeek / OpenAI / Kimi / 通义 / 硅基流动 …），或 Anthropic Messages API
- **文献**：OpenAlex / Crossref / arXiv / Semantic Scholar

---

## 2. 架构 | Architecture

```
┌─────────────────────────── 浏览器 (React SPA) ───────────────────────────┐
│  登录 / 工作台 / 新建论文 / 论文查看器（编辑·重写·导出） / 文献检索 / 设置  │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │ HTTPS · JWT
┌───────────────────────────────▼──────────────────────────────────────────┐
│                         FastAPI (backend/app)                             │
│  routers: auth · papers · literature · meta                              │
│  services: pipeline(生成流水线) · llm(模型适配) · literature(检索)         │
│            citations(引用格式) · export(docx/pdf/md/bib)                  │
│  SQLite: users · papers · events · literature_cache                      │
└───────┬───────────────────────────────┬──────────────────────────────────┘
        │                               │
┌───────▼────────┐              ┌───────▼──────────────────────────────────┐
│  LLM Provider  │              │  OpenAlex · Crossref · arXiv · S2        │
│ (OpenAI 兼容)   │              │  (真实文献元数据)                         │
└────────────────┘              └──────────────────────────────────────────┘
```

**生成流水线**：`researching → outlining → writing(×6) → abstract → references → completed`。
每节生成后立即落库，任何一步失败都已保留已完成的内容，可直接重试或续写。

---

## 3. 快速开始（本地）| Quick start

```bash
git clone https://github.com/lostbefore/Academic-Paper-Assistant.git
cd Academic-Paper-Assistant

# 1) 配置
cp .env.example .env
#    填入 LLM_API_KEY（例如 DeepSeek：https://api.deepseek.com/v1，模型 deepseek-chat）
#    设置 ADMIN_EMAIL / ADMIN_PASSWORD

# 2) 后端
python -m venv .venv
.venv/Scripts/pip install -r backend/requirements.txt      # Windows
# source .venv/bin/activate && pip install -r backend/requirements.txt   # macOS/Linux
python start.py            # http://127.0.0.1:8000

# 3) 前端（开发模式，可选）
cd frontend
npm install
npm run dev                # http://127.0.0.1:3000 ，/api 已代理到 8000
```

生产模式只需先构建前端，后端会在同一端口托管静态资源：

```bash
cd frontend && npm ci && npm run build && cd ..
python start.py            # 直接访问 http://127.0.0.1:8000
```

---

## 4. 配置项 | Configuration

所有配置来自 `.env`（参考 `.env.example`）：

| 变量 | 默认 | 说明 |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai`（任意兼容接口）或 `anthropic` |
| `LLM_API_KEY` | — | 模型密钥（必填） |
| `LLM_BASE_URL` | `https://api.deepseek.com/v1` | OpenAI 兼容的 base url |
| `LLM_MODEL` | `deepseek-chat` | 主模型 |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | — | 空库时自动创建的管理员 |
| `ALLOW_REGISTRATION` | `true` | 是否开放注册 |
| `JWT_SECRET` | 自动生成 | 留空则生成并保存在 `data/jwt_secret` |
| `MAX_CONCURRENT_JOBS` | `2` | 同时生成的论文数 |
| `DATA_DIR` | `./data` | SQLite 与导出文件目录 |
| `SEMANTIC_SCHOLAR_API_KEY` | 空 | 配置后自动启用第四个文献源 |

> 相对路径一律相对仓库根目录解析，因此从任何工作目录启动行为一致。

---

## 5. 主要接口 | API

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/auth/register` · `/api/auth/login` | 注册 / 登录，返回 JWT |
| GET | `/api/auth/me` | 当前用户 |
| GET/POST | `/api/papers` | 列表 / 创建（异步生成，202） |
| GET/PATCH/DELETE | `/api/papers/{id}` | 详情 / 局部更新 / 删除 |
| POST | `/api/papers/{id}/cancel` · `/retry` | 取消 / 重试 |
| PUT | `/api/papers/{id}/sections/{key}` | 保存章节 |
| POST | `/api/papers/{id}/sections/{key}/regenerate` | 重写章节 |
| GET | `/api/papers/{id}/events` | SSE 进度流 |
| GET | `/api/papers/{id}/export/{docx\|pdf\|md\|bib}` | 导出 |
| GET | `/api/literature/search` | 文献检索 |
| GET | `/api/status` · `/api/health` · `/api/stats` | 状态 / 健康 / 统计 |
| POST | `/api/llm/test` | 模型连通性自检 |

交互式文档：`/api/docs`。

---

## 6. 部署到服务器 | Deployment

Ubuntu 22.04 示例（单机、systemd、80 端口）：

```bash
# 本地构建前端后同步到服务器
cd frontend && npm ci && npm run build && cd ..
scp -r . root@<server>:/opt/academic-paper-assistant

# 服务器上
ssh root@<server>
cd /opt/academic-paper-assistant
cp .env.example .env && vim .env      # 填 LLM_API_KEY / ADMIN_*
bash deploy/install.sh
```

`install.sh` 会创建 `apa` 用户、建立 venv、安装依赖、注册并启动 `apa.service`
（`AmbientCapabilities=CAP_NET_BIND_SERVICE`，非 root 监听 80）。

**云主机还需在安全组放行 80 端口**，否则外网无法访问。

常用运维命令：

```bash
systemctl status apa          # 运行状态
journalctl -u apa -f          # 实时日志
systemctl restart apa         # 重启
```

---

## 7. 目录结构 | Layout

```
backend/
  app/
    main.py             # 应用入口、静态资源托管、启动自检
    config.py           # 环境变量配置
    db.py               # SQLite 访问层与建表
    security.py         # bcrypt + JWT
    schemas.py          # Pydantic 模型
    deps.py             # 鉴权依赖
    routers/            # auth / papers / literature / meta
    services/           # llm / literature / prompts / pipeline / citations / export
  tests/                # 37 条 pytest 用例
  requirements.txt
frontend/               # React + TS + Vite
knowledge/              # 学术写作与引用规范的参考知识库
deploy/                 # systemd 单元与安装脚本
docs/                   # 设计文档、测试记录与附录（见 docs/README.md）
legacy/                 # v1 命令行版本（保留用于历史对照）
start.py                # 一键启动
```

## 7.1 文档 | Documentation

设计与开发过程材料见 [`docs/`](docs/README.md)：

| 文档 | 内容 |
|---|---|
| [00 开发过程记录](docs/00-开发过程记录.md) | 从立项到上线的阶段、缺陷与验证过程 |
| [01 需求分析](docs/01-需求分析与项目概述.md) | 背景、用户、25 条功能需求、验收标准 |
| [02 系统架构](docs/02-系统架构设计.md) | 逻辑/部署架构、技术选型、6 个关键决策 |
| [03 数据库设计](docs/03-数据库设计.md) | 四张表、JSON 字段、状态机 |
| [04 接口设计](docs/04-接口设计.md) | 22 个接口、SSE 协议 |
| [05 生成流水线](docs/05-生成流水线设计.md) | 六阶段、提示词结构、长度与引用控制 |
| [06 关键模块](docs/06-关键模块设计.md) | 模型适配、文献检索、引用格式、导出 |
| [07 前端设计](docs/07-前端设计.md) | 页面结构、状态管理、交互 |
| [08 测试记录](docs/08-测试方案与测试记录.md) | 37 条用例、6 个真实缺陷、性能数据 |
| [09 部署运维](docs/09-部署与运维.md) | 服务器部署、systemd、验证记录 |
| [10 版本演进](docs/10-版本演进与变更记录.md) | v1 → v2 完整变更 |
| [11 学术诚信](docs/11-学术诚信与使用边界.md) | 防幻觉约束与使用规范 |

汇编版：[`docs/学术论文助手-设计与开发文档集.pdf`](docs/学术论文助手-设计与开发文档集.pdf)（80 页，含封面、11 篇文档与 4 个附录）。

---

## 8. 设计原则与边界 | Principles & limits

1. **不编造数据**：提示词明确禁止虚构统计量、实验结果与文献；没有检索到文献时正文不做引用标注。
2. **引用可溯源**：参考文献全部来自检索结果，条目前可跳转 DOI/原文。
3. **过程可复核**：每次生成与编辑都有事件日志，便于作者自查与披露 AI 使用情况。
4. **作者负责**：生成内容必须经作者核对、修改后方可使用；本系统是写作辅助工具，不是代写服务。

已知限制：生成的「研究结果」章节是对研究设计的推演式论述，**不产生真实实验数据**，
不可直接作为实证结论使用；PDF 中文字体采用 CID 字体，个别阅读器可能提示缺失字体。

---

## 9. 许可证 | License

MIT License — 见 [LICENSE](LICENSE)。

## 10. 免责声明 | Disclaimer

本工具仅供学习与研究用途。使用者应遵守所在机构与期刊关于生成式人工智能使用的规定，
并对最终提交内容承担全部责任。
