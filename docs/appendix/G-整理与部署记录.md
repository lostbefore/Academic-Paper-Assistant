# 附录 G · 2026-11-16 整理与部署记录

> 本附录记录 2026 年 11 月 16 日完成的代码整理、服务器配置与上线验证，不计入 2026 年 3–6 月的开发周期（见第 00 章）。

## G.1 整理范围

在原有设计的基础上，对应用层做了整理与补齐，使系统具备可部署、可测试、可追溯的形态：

| 模块 | 整理内容 | 位置 |
|---|---|---|
| 配置与存储 | 环境变量集中解析；SQLite（WAL）四表；JSON 字段承载提纲与章节 | `app/config.py`、`app/db.py` |
| 账户 | 邮箱注册登录、bcrypt、JWT、按用户隔离论文 | `app/security.py`、`routers/auth.py` |
| 生成流水线 | 检索 → 提纲 → 分节写作 → 摘要 → 文献表；逐节落库；取消/重试 | `services/pipeline.py` |
| 实时进度 | SSE 增量推送，按事件 id 断点续传 | `routers/papers.py` |
| 章节编辑 | 单节保存、带指令重写 | `routers/papers.py` |
| 导出 | DOCX / PDF / Markdown / BibTeX 重写 | `services/export.py` |
| 文献 | OpenAlex + Crossref + arXiv 合并、排序、缓存 | `services/literature.py` |
| 测试 | 6 个文件、37 条用例 | `backend/tests/` |
| 文档 | 12 篇文档 + 7 个附录，汇编为单文件 PDF | `docs/` |

整理后的版本号为 **v2.0.0**，同日提交并推送至 GitHub。

## G.2 服务器配置

| 项目 | 配置 |
|---|---|
| 操作系统 | Ubuntu 22.04 LTS |
| 规格 | 1 核 / 1.7 GB 内存 / 40 GB 磁盘 |
| 代码目录 | `/opt/academic-paper-assistant` |
| 运行方式 | systemd 单元 `apa.service`，`Restart=always` |
| 运行用户 | 系统用户 `apa`（非 root），仅授予 `CAP_NET_BIND_SERVICE` 以绑定 80 端口 |
| Python 环境 | `.venv`（Python 3.10.12），依赖来自 `backend/requirements.txt` |
| 前端 | 本地构建后上传 `frontend/dist`，由后端同端口托管，服务器不安装 Node |
| 数据 | `data/apa.db`、`data/exports/`、`data/jwt_secret`，属主 `apa` |
| 配置 | `.env` 权限 600、属主 `apa` |

systemd 关键参数：

```ini
User=apa
WorkingDirectory=/opt/academic-paper-assistant/backend
EnvironmentFile=/opt/academic-paper-assistant/.env
ExecStart=/opt/academic-paper-assistant/.venv/bin/python -m uvicorn \
    app.main:app --host 0.0.0.0 --port 80 --proxy-headers --forwarded-allow-ips=*
Restart=always
AmbientCapabilities=CAP_NET_BIND_SERVICE
NoNewPrivileges=true
```

安装脚本 `deploy/install.sh` 将上述步骤固化：创建用户 → 建 venv → 装依赖 → 修权限 → 装单元 → 启动 → 健康检查。

## G.3 整理中修复的缺陷

| 编号 | 现象 | 根因 | 修复 |
|---|---|---|---|
| BUG-01 | 创建论文返回 500 | 路由写成同步函数，线程内没有事件循环，create_task 失败 | 改为 sync def |
| BUG-02 | 英文作者姓名颠倒（Ashish, V.） | 姓名解析取错姓氏位置 | 取最后一段为姓氏，并支持 Family, Given 形式 |
| BUG-03 | 中文论文长度 1.9 倍超标 | token 预算按英文估算、提示词用词不当、提纲字数未重标定 | 分语言预算 + 汉字区间 + 提纲重标定 |
| BUG-04 | 前端构建不通过 | 未使用导入、类型缺失、字段引用错误 | 修正导入与类型声明 |

## G.4 部署中发现的问题

| 编号 | 现象 | 根因 | 修复 |
|---|---|---|---|
| BUG-05 | 服务反复重启（`activating (auto-restart)`），日志报 `PermissionError: '/opt/.../.env'` | 安装脚本只收紧权限未改属主，服务以 `apa` 运行读不到 root 的 600 文件 | 先 `chown apa:apa .env` 再 `chmod 600` |
| BUG-06 | 本机访问正常、外网超时；`ufw` 未启用、`iptables` 默认 ACCEPT | 云平台安全组未放行 80 端口 | 控制台添加入站规则 `TCP:80`，来源 `0.0.0.0/0` |

## G.5 验证记录

| 时间 | 动作 | 结果 |
|---|---|---|
| 14:33 | 打包上传（排除 `node_modules`、`.venv`、`data`） | 668 KB |
| 14:34 | 首次启动 `apa.service` | 失败：`.env` 权限 |
| 14:34 | 修正属主后重启 | `active (running)` |
| 14:36 | SSH 隧道内端到端验证 | 登录 → 生成 2855 字 → 四种导出成功 |
| 14:58 | 修复引用格式后重新部署后端 | 健康检查 ok |
| 15:41 | 公网端到端验证 | 登录 → 生成 2845 字 → DOCX/PDF/MD/BibTeX 均 200 |
| 15:51 | 安全组放行后外部复验 | `GET /api/health` 返回 200 |

公网验证摘要：

| 检查项 | 结果 |
|---|---|
| `GET /api/health` | `{"status":"ok","database":"ok","llm_configured":true,"version":"2.0.0"}` |
| `GET /` | 200，返回 SPA 入口 |
| `GET /assets/index-*.js` | 200，443,467 字节 |
| `POST /api/auth/login` | 200，返回 JWT |
| 端到端生成 | 2845 字，8 篇文献，耗时 24 秒 |

## G.6 资源占用

| 指标 | 数值 |
|---|---|
| 常驻内存 | 43 MB |
| 部署目录 | 105 MB（含 venv） |
| 磁盘剩余 | 25 GB |

## G.7 说明

本附录只记录整理与上线当天的工作，目的是让评审能够区分「开发期完成的设计与实现」与「上线前完成的工程化整理」。开发期的过程、缺陷与测试见第 00 章；部署与运维的通用方法见第 09 章。
