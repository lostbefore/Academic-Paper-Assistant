# 附录 B · HTTP 接口清单

> 由 FastAPI 自动生成的 OpenAPI 文档导出，共 22 个接口。交互式文档见部署实例 `/api/docs`。

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/me` | Me |
| POST | `/api/auth/register` | Register |
| GET | `/api/health` | Health |
| GET | `/api/literature/search` | Search |
| GET | `/api/literature/sources` | Sources |
| POST | `/api/llm/test` | Llm Test |
| GET | `/api/papers` | List Papers |
| POST | `/api/papers` | Create Paper |
| DELETE | `/api/papers/{paper_id}` | Delete Paper |
| GET | `/api/papers/{paper_id}` | Get Paper |
| PATCH | `/api/papers/{paper_id}` | Patch Paper |
| POST | `/api/papers/{paper_id}/cancel` | Cancel Paper |
| GET | `/api/papers/{paper_id}/events` | Paper Events |
| GET | `/api/papers/{paper_id}/export/{fmt}` | Export Paper |
| GET | `/api/papers/{paper_id}/log` | Paper Log |
| POST | `/api/papers/{paper_id}/retry` | Retry Paper |
| PUT | `/api/papers/{paper_id}/sections/{section_key}` | Update Section |
| POST | `/api/papers/{paper_id}/sections/{section_key}/regenerate` | Regenerate Section |
| GET | `/api/stats` | Stats |
| GET | `/api/status` | Status |
| GET | `/api/styles` | Styles |
