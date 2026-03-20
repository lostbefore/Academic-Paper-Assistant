# 学术论文助手 (Academic Paper Assistant)

> AI 驱动的学术论文生成器，集成智能图片系统和多源研究能力。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6.svg)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.0-38B2AC.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[返回主页](README.md) | [English Version](README_EN.md)

---

## 功能特点

### 核心功能
- **AI 论文生成**: 使用 Claude AI 生成完整的学术论文，包含摘要、引言、文献综述、研究方法、结果、讨论、结论和参考文献
- **多语言支持**: 支持英文和中文论文生成，符合学术格式规范
- **引用格式**: 支持 APA、MLA、IEEE 和 GB/T 7714（中国标准）引用格式
- **文献整合**: 从 Semantic Scholar 数据库自动检索和引用文献

### 智能图片系统
- **AI 生成图表**: 使用 Mermaid.js 和 Matplotlib 创建数据可视化和流程图
- **网络图片搜索**: 从 DuckDuckGo、Serper、Bing 和 Unsplash 搜索并整合相关学术图片
- **PDF 图片提取**: 从现有学术论文中提取图表和图片
- **自动图片定位**: 智能将图片放置在论文的合适章节

### 导出选项
- **PDF**: 专业格式的 PDF 输出（需要 LibreOffice 或 Microsoft Word）
- **DOCX**: Microsoft Word 格式，包含适当的样式
- **Markdown**: 原始 Markdown 格式供进一步编辑

### Web 界面
- **现代化界面**: React + TypeScript + Tailwind CSS 前端
- **黑夜模式**: 完整的深色主题支持
- **双语界面**: 中英文界面切换
- **实时预览**: 格式化的论文预览，支持章节导航
- **来源标注**: 专门的页面展示所有参考文献和图片来源

---

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- Anthropic API Key (Claude)

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/lostbefore/Academic-Paper-Assistant.git
   cd Academic-Paper-Assistant
   ```

2. **配置 Python 环境**
   ```bash
   # 创建虚拟环境
   python -m venv .venv

   # 激活环境 (Windows)
   .venv\Scripts\activate
   # 或者 (Linux/Mac)
   source .venv/bin/activate

   # 安装依赖
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   ```bash
   # 手动创建 .env 文件，填入以下 API 密钥
   ANTHROPIC_API_KEY=你的_claude_api_key
   SEMANTIC_SCHOLAR_API_KEY=你的_semantic_scholar_key
   SERPER_API_KEY=你的_serper_key
   UNSPLASH_ACCESS_KEY=你的_unsplash_key
   ```

4. **配置前端**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

### 运行应用

**方式 1：仅运行后端**
```bash
python backend/api.py
```
后端地址：`http://localhost:8000`

**方式 2：开发模式（热重载）**
```bash
cd frontend
npm run dev
```
前端地址：`http://localhost:5173`

**方式 3：生产构建**
```bash
cd frontend
npm run build
```

---

## 项目结构

```
academic-paper-assistant/
├── backend/              # FastAPI 后端
│   ├── api.py           # 主 API 接口
│   ├── docx_generator.py
│   └── output/          # 生成的论文
├── frontend/            # React 前端
│   ├── src/
│   │   ├── pages/       # 页面组件
│   │   ├── components/  # 可复用组件
│   │   ├── i18n/        # 国际化
│   │   └── services/    # API 服务
│   └── public/
├── agents/              # 论文生成 AI 代理
├── skills/              # 专项技能
│   ├── image_search.py      # 图片搜索功能
│   ├── chart_generator.py   # 图表生成
│   ├── pdf_image_extractor.py
│   └── literature_search.py
├── knowledge/           # 知识库
├── output/             # 输出目录
├── config.py           # 配置文件
├── requirements.txt    # Python 依赖
└── .env               # 环境变量
```

---

## 配置说明

### 必需的 API 密钥

| 服务 | 用途 | 获取地址 |
|---------|---------|---------|
| Anthropic Claude | AI 论文生成 | [控制台](https://console.anthropic.com/) |
| Semantic Scholar | 学术文献搜索 | [官网](https://www.semanticscholar.org/product/api) |
| Serper | Google 图片搜索 | [控制台](https://serper.dev/) |
| Unsplash | 高质量免费图片 | [开发者](https://unsplash.com/developers) |
| Bing Image | 图片搜索备选 | [Azure](https://azure.microsoft.com/) |

### 环境变量

查看 `.env` 文件了解所有可用选项：
- `ANTHROPIC_API_KEY` - 论文生成必需
- `ANTHROPIC_MODEL` - 使用的模型（默认：claude-sonnet-4-6-20251001）
- `DEFAULT_CITATION_STYLE` - 默认引用格式：apa
- `ENABLE_IMAGES` - 启用图片生成（默认：true）
- `MAX_IMAGES_PER_PAPER` - 每篇论文最大图片数（默认：3）
- `IMAGE_SOURCES` - 图片来源（逗号分隔）：ai_generate,pdf_extract,web_search

---

## 使用指南

### Web 界面

1. **创建新论文**
   - 导航到"新建论文"
   - 输入标题、关键词和领域
   - 选择语言和引用格式
   - 点击"生成"

2. **监控进度**
   - 实时查看生成进度
   - 阶段指示器（文献调研 → 写作中 → 完成）

3. **预览和导出**
   - 查看格式化论文，支持章节导航
   - 切换普通预览和格式化预览
   - 查看参考文献和图片来源
   - 下载为 PDF、DOCX 或 Markdown

### API 接口

- `POST /api/papers` - 创建新论文
- `GET /api/papers/{id}` - 获取论文详情
- `GET /api/papers/{id}/download/pdf` - 下载 PDF
- `GET /api/papers/{id}/download/docx` - 下载 DOCX
- `GET /api/papers/{id}/download/md` - 下载 Markdown
- `GET /api/status` - API 状态和配置

---

## 开发指南

### 运行测试

```bash
# 测试图片搜索功能
python test_image_search.py

# 测试完整图片系统
python test_image_system.py

# 测试中文格式
python test_chinese_format.py
```

### 添加新功能

1. **新图片来源**: 在 `skills/image_search.py` 中添加方法
2. **新图表类型**: 扩展 `skills/chart_generator.py`
3. **新引用格式**: 更新 `knowledge/citation_styles/`
4. **新语言**: 在 `frontend/src/i18n/translations.ts` 中添加翻译

---

## 技术栈

### 后端
- **FastAPI** - 现代 Python Web 框架
- **Pydantic** - 数据验证
- **aiohttp** - 异步 HTTP 客户端
- **python-docx** - Word 文档生成
- **PyMuPDF** - PDF 处理
- **Pillow** - 图像处理
- **matplotlib** - 图表生成

### 前端
- **React 18** - UI 库
- **TypeScript** - 类型安全的 JavaScript
- **Tailwind CSS** - 原子化 CSS
- **Vite** - 构建工具
- **React Router** - 路由导航
- **Lucide React** - 图标库

### AI & 外部 API
- **Anthropic Claude** - 大语言模型
- **Semantic Scholar** - 学术文献
- **DuckDuckGo** - 网页搜索
- **Serper** - Google 搜索 API
- **Unsplash** - 免费图片
- **Mermaid.js** - 图表生成

---

## 贡献指南

欢迎贡献！请随时提交 Pull Request。

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

---

## 开源协议

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 致谢

- [Anthropic](https://www.anthropic.com/) 提供 Claude AI
- [Semantic Scholar](https://www.semanticscholar.org/) 提供学术文献 API
- [Unsplash](https://unsplash.com/) 提供免费高质量图片
- [Mermaid.js](https://mermaid.js.org/) 提供图表生成

---

## 技术支持

如果你遇到任何问题或有疑问：

1. 查看 [Issues](https://github.com/lostbefore/Academic-Paper-Assistant/issues) 页面
2. 创建新 issue，提供详细描述
3. 包含相关日志和配置（API 密钥需打码）

---

**免责声明**: 本工具仅供教育和研究用途。用户有责任确保使用符合学术诚信政策和适用法规。生成的论文应作为参考或起点，未经适当审查和修改不得作为原创作品提交。
