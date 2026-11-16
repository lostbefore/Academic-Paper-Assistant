# 附录 A · 代码与文件统计

> 统计时间：2026-11-16　统计范围：仓库工作区（不含 .git / node_modules / dist / data）

## A.1 按模块汇总

| 模块 | 行数 |
|---|---:|
| legacy（v1 归档） | 8309 |
| backend | 3728 |
| frontend | 3017 |
| 根目录 | 713 |
| docs | 599 |
| deploy | 74 |
| **合计** | **16440** |

## A.2 文件明细

| 文件 | 类型 | 字节 | 行数 |
|---|---|---:|---:|
| `README.md` | Markdown | 10009 | 210 |
| `backend/.pytest_cache/README.md` | Markdown | 302 | 8 |
| `backend/api.py` | Python | 198 | 7 |
| `backend/app/__init__.py` | Python | 0 | 0 |
| `backend/app/config.py` | Python | 5426 | 143 |
| `backend/app/db.py` | Python | 4471 | 145 |
| `backend/app/deps.py` | Python | 1969 | 53 |
| `backend/app/main.py` | Python | 4446 | 140 |
| `backend/app/routers/__init__.py` | Python | 0 | 0 |
| `backend/app/routers/auth.py` | Python | 2314 | 63 |
| `backend/app/routers/literature.py` | Python | 1161 | 37 |
| `backend/app/routers/meta.py` | Python | 3008 | 94 |
| `backend/app/routers/papers.py` | Python | 15888 | 430 |
| `backend/app/schemas.py` | Python | 3729 | 142 |
| `backend/app/security.py` | Python | 1451 | 46 |
| `backend/app/services/__init__.py` | Python | 0 | 0 |
| `backend/app/services/citations.py` | Python | 5396 | 176 |
| `backend/app/services/export.py` | Python | 11739 | 306 |
| `backend/app/services/literature.py` | Python | 12359 | 324 |
| `backend/app/services/llm.py` | Python | 9506 | 267 |
| `backend/app/services/pipeline.py` | Python | 19128 | 528 |
| `backend/app/services/prompts.py` | Python | 8187 | 230 |
| `backend/tests/conftest.py` | Python | 1595 | 56 |
| `backend/tests/test_api.py` | Python | 6516 | 158 |
| `backend/tests/test_citations.py` | Python | 1799 | 64 |
| `backend/tests/test_export.py` | Python | 3138 | 92 |
| `backend/tests/test_literature.py` | Python | 3581 | 98 |
| `backend/tests/test_pipeline.py` | Python | 2625 | 62 |
| `backend/tests/test_security.py` | Python | 1649 | 59 |
| `deploy/apa.service` | systemd | 610 | 21 |
| `deploy/install.sh` | Shell | 1616 | 53 |
| `docs/01-需求分析与项目概述.md` | Markdown | 8085 | 145 |
| `docs/README.md` | Markdown | 4045 | 57 |
| `docs/appendix/A-代码统计.md` | Markdown | 5987 | 115 |
| `docs/appendix/B-接口清单.md` | Markdown | 1271 | 28 |
| `docs/appendix/C-数据库结构.md` | Markdown | 2146 | 90 |
| `docs/appendix/D-提交历史.md` | Markdown | 715 | 12 |
| `docs/build_appendix.py` | Python | 5586 | 152 |
| `frontend/index.html` | HTML | 386 | 13 |
| `frontend/package.json` | JSON | 1041 | 36 |
| `frontend/src/App.tsx` | TypeScript (React) | 5978 | 143 |
| `frontend/src/components/LanguageSwitcher.tsx` | TypeScript (React) | 658 | 19 |
| `frontend/src/components/ThemeToggle.tsx` | TypeScript (React) | 779 | 21 |
| `frontend/src/contexts/AuthContext.tsx` | TypeScript (React) | 2200 | 77 |
| `frontend/src/contexts/ThemeContext.tsx` | TypeScript (React) | 2363 | 85 |
| `frontend/src/i18n/LanguageContext.tsx` | TypeScript (React) | 2839 | 87 |
| `frontend/src/i18n/index.ts` | TypeScript | 200 | 3 |
| `frontend/src/i18n/translations.ts` | TypeScript | 11615 | 376 |
| `frontend/src/index.css` | CSS | 2351 | 83 |
| `frontend/src/main.tsx` | TypeScript (React) | 443 | 16 |
| `frontend/src/pages/CreatePaper.tsx` | TypeScript (React) | 14162 | 329 |
| `frontend/src/pages/Dashboard.tsx` | TypeScript (React) | 8476 | 194 |
| `frontend/src/pages/Literature.tsx` | TypeScript (React) | 6711 | 146 |
| `frontend/src/pages/Login.tsx` | TypeScript (React) | 7122 | 152 |
| `frontend/src/pages/PaperList.tsx` | TypeScript (React) | 8928 | 201 |
| `frontend/src/pages/PaperViewer.tsx` | TypeScript (React) | 21857 | 478 |
| `frontend/src/pages/Settings.tsx` | TypeScript (React) | 7052 | 145 |
| `frontend/src/services/api.ts` | TypeScript | 6945 | 211 |
| `frontend/src/types/index.ts` | TypeScript | 3389 | 147 |
| `frontend/src/vite-env.d.ts` | TypeScript | 158 | 9 |
| `frontend/tsconfig.json` | JSON | 581 | 21 |
| `frontend/tsconfig.node.json` | JSON | 221 | 10 |
| `frontend/vite.config.ts` | TypeScript | 293 | 15 |
| `knowledge/citation_rules.md` | Markdown | 6253 | 219 |
| `knowledge/paper_structure.md` | Markdown | 6091 | 246 |
| `legacy/DEPLOY.md` | Markdown | 9229 | 419 |
| `legacy/DEPLOY_WINDOWS.md` | Markdown | 5544 | 253 |
| `legacy/README_EN.md` | Markdown | 9265 | 287 |
| `legacy/README_ZH.md` | Markdown | 8630 | 286 |
| `legacy/START_GUIDE.md` | Markdown | 1990 | 110 |
| `legacy/agents/__init__.py` | Python | 172 | 6 |
| `legacy/agents/researcher_agent.py` | Python | 17448 | 512 |
| `legacy/agents/writer_agent.py` | Python | 33294 | 834 |
| `legacy/commands/format.py` | Python | 8769 | 276 |
| `legacy/commands/new_paper.py` | Python | 8066 | 256 |
| `legacy/config.py` | Python | 4622 | 107 |
| `legacy/docker-compose.yml` | YAML | 1337 | 46 |
| `legacy/docx_generator.py` | Python | 38911 | 943 |
| `legacy/main.py` | Python | 3031 | 95 |
| `legacy/plugin/__init__.py` | Python | 152 | 5 |
| `legacy/plugin/paper_plugin.py` | Python | 6317 | 151 |
| `legacy/skills/__init__.py` | Python | 265 | 7 |
| `legacy/skills/academic_rules.py` | Python | 15255 | 389 |
| `legacy/skills/chart_generator.py` | Python | 10664 | 360 |
| `legacy/skills/formatting.py` | Python | 14530 | 484 |
| `legacy/skills/image_search.py` | Python | 23152 | 636 |
| `legacy/skills/literature_search.py` | Python | 13115 | 360 |
| `legacy/skills/pdf_image_extractor.py` | Python | 9030 | 263 |
| `legacy/test.py` | Python | 16653 | 511 |
| `legacy/test_chinese_format.py` | Python | 9961 | 35 |
| `legacy/test_image_search.py` | Python | 5859 | 174 |
| `legacy/test_image_system.py` | Python | 9055 | 295 |
| `legacy/test_literature_search.py` | Python | 7341 | 209 |
| `start.py` | Python | 966 | 38 |
