# Academic Paper Assistant

> AI-powered academic paper generator with intelligent image integration and multi-source research capabilities.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6.svg)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.0-38B2AC.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[Back to Main](README.md) | [中文版](README_ZH.md)

---

## Features

### Core Capabilities
- **AI-Powered Paper Generation**: Generate complete academic papers using Claude AI with structured sections (Abstract, Introduction, Literature Review, Methodology, Results, Discussion, Conclusion, References)
- **Multi-Language Support**: Generate papers in English or Chinese with proper academic formatting
- **Citation Styles**: Support for APA, MLA, IEEE, and GBT7714 (Chinese standard)
- **Literature Integration**: Automatic research and citation from Semantic Scholar database

### Intelligent Image System
- **AI-Generated Charts**: Create data visualizations and flowcharts using Mermaid.js and Matplotlib
- **Web Image Search**: Search and integrate relevant academic images from DuckDuckGo, Serper, Bing, and Unsplash
- **PDF Image Extraction**: Extract figures and images from existing academic papers
- **Automatic Image Placement**: Smart positioning of images within appropriate paper sections

### Export Options
- **PDF**: Professional formatted PDF output (requires LibreOffice or Microsoft Word)
- **DOCX**: Microsoft Word format with proper styling
- **Markdown**: Raw markdown for further editing

### Web Interface
- **Modern UI**: React + TypeScript + Tailwind CSS frontend
- **Dark Mode**: Full dark theme support
- **Bilingual Interface**: English and Chinese UI
- **Real-time Preview**: Formatted paper preview with section navigation
- **Source Attribution**: Dedicated page showing all references and image sources

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Anthropic API Key (Claude)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/lostbefore/Academic-Paper-Assistant.git
   cd Academic-Paper-Assistant
   ```

2. **Set up Python environment**
   ```bash
   # Create virtual environment
   python -m venv .venv

   # Activate (Windows)
   .venv\Scripts\activate
   # Or (Linux/Mac)
   source .venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   # Create .env file manually or copy from example
   # Edit .env with your API keys
   ANTHROPIC_API_KEY=your_claude_api_key_here
   SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_key_here
   SERPER_API_KEY=your_serper_key_here
   UNSPLASH_ACCESS_KEY=your_unsplash_key_here
   ```

4. **Set up frontend**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

### Running the Application

**Option 1: Run backend only**
```bash
python backend/api.py
```
Backend will be available at `http://localhost:8000`

**Option 2: Run with hot reload (development)**
```bash
cd frontend
npm run dev
```
Frontend will be available at `http://localhost:5173`

**Option 3: Full production build**
```bash
cd frontend
npm run build
```

---

## Project Structure

```
academic-paper-assistant/
├── backend/              # FastAPI backend
│   ├── api.py           # Main API endpoints
│   ├── docx_generator.py
│   └── output/          # Generated papers
├── frontend/            # React frontend
│   ├── src/
│   │   ├── pages/       # Page components
│   │   ├── components/  # Reusable components
│   │   ├── i18n/        # Internationalization
│   │   └── services/    # API services
│   └── public/
├── agents/              # AI agents for paper generation
├── skills/              # Specialized skills
│   ├── image_search.py      # Image search functionality
│   ├── chart_generator.py   # Chart generation
│   ├── pdf_image_extractor.py
│   └── literature_search.py
├── knowledge/           # Knowledge base
├── output/             # Output directory
├── config.py           # Configuration
├── requirements.txt    # Python dependencies
└── .env               # Environment variables
```

---

## Configuration

### Required API Keys

| Service | Purpose | Get Key |
|---------|---------|---------|
| Anthropic Claude | AI paper generation | [Console](https://console.anthropic.com/) |
| Semantic Scholar | Academic literature search | [Website](https://www.semanticscholar.org/product/api) |
| Serper | Google image search | [Dashboard](https://serper.dev/) |
| Unsplash | High-quality stock images | [Developers](https://unsplash.com/developers) |
| Bing Image | Image search alternative | [Azure](https://azure.microsoft.com/) |

### Environment Variables

See `.env` file for all available options:
- `ANTHROPIC_API_KEY` - Required for paper generation
- `ANTHROPIC_MODEL` - Model to use (default: claude-sonnet-4-6-20251001)
- `DEFAULT_CITATION_STYLE` - Default: apa
- `ENABLE_IMAGES` - Enable image generation (default: true)
- `MAX_IMAGES_PER_PAPER` - Maximum images (default: 3)
- `IMAGE_SOURCES` - Comma-separated: ai_generate,pdf_extract,web_search

---

## Usage

### Web Interface

1. **Create a New Paper**
   - Navigate to "New Paper"
   - Enter title, keywords, and field
   - Select language and citation style
   - Click "Generate"

2. **Monitor Progress**
   - Real-time generation progress
   - Stage indicators (Research → Writing → Complete)

3. **Preview and Export**
   - View formatted paper with section navigation
   - Switch between plain and formatted preview
   - View references and image sources
   - Download as PDF, DOCX, or Markdown

### API Endpoints

- `POST /api/papers` - Create new paper
- `GET /api/papers/{id}` - Get paper by ID
- `GET /api/papers/{id}/download/pdf` - Download PDF
- `GET /api/papers/{id}/download/docx` - Download DOCX
- `GET /api/papers/{id}/download/md` - Download Markdown
- `GET /api/status` - API status and configuration

---

## Development

### Running Tests

```bash
# Test image search functionality
python test_image_search.py

# Test complete image system
python test_image_system.py

# Test Chinese formatting
python test_chinese_format.py
```

### Adding New Features

1. **New Image Source**: Add method in `skills/image_search.py`
2. **New Chart Type**: Extend `skills/chart_generator.py`
3. **New Citation Style**: Update `knowledge/citation_styles/`
4. **New Language**: Add translations in `frontend/src/i18n/translations.ts`

---

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation
- **aiohttp** - Async HTTP client
- **python-docx** - Word document generation
- **PyMuPDF** - PDF processing
- **Pillow** - Image processing
- **matplotlib** - Chart generation

### Frontend
- **React 18** - UI library
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS
- **Vite** - Build tool
- **React Router** - Navigation
- **Lucide React** - Icons

### AI & External APIs
- **Anthropic Claude** - Large language model
- **Semantic Scholar** - Academic literature
- **DuckDuckGo** - Web search
- **Serper** - Google search API
- **Unsplash** - Stock images
- **Mermaid.js** - Diagram generation

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [Anthropic](https://www.anthropic.com/) for Claude AI
- [Semantic Scholar](https://www.semanticscholar.org/) for academic literature API
- [Unsplash](https://unsplash.com/) for free high-quality images
- [Mermaid.js](https://mermaid.js.org/) for diagram generation

---

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/lostbefore/Academic-Paper-Assistant/issues) page
2. Create a new issue with detailed description
3. Include relevant logs and configuration (with API keys redacted)

---

**Disclaimer**: This tool is for educational and research purposes. Users are responsible for ensuring their use complies with academic integrity policies and applicable laws. Generated papers should be used as references or starting points, not submitted as original work without proper review and modification.
