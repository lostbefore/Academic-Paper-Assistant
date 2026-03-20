"""
FastAPI Backend for Academic Paper Assistant

Provides REST API endpoints for the React frontend.
"""

import os
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from docx_generator import DocxGenerator, generate_docx

from agents.researcher_agent import ResearchAgent
from agents.writer_agent import WriterAgent
from skills.literature_search import LiteratureSearchSkill
from skills.academic_rules import AcademicRulesSkill
from skills.formatting import FormattingSkill
from skills.image_search import ImageSearchSkill
from skills.chart_generator import ChartGeneratorSkill
from skills.pdf_image_extractor import PDFImageExtractor

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

app = FastAPI(
    title="Academic Paper Assistant API",
    description="AI-powered academic paper generation API",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store generated papers in memory (in production, use a database)
papers_db: Dict[str, Dict[str, Any]] = {}

# Initialize components
api_key = os.getenv("ANTHROPIC_API_KEY")
api_base = os.getenv("ANTHROPIC_API_BASE", "")
model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6-20251001")

literature_skill = LiteratureSearchSkill()
academic_rules_skill = AcademicRulesSkill()
formatting_skill = FormattingSkill()
image_skill = ImageSearchSkill()
pdf_extractor = PDFImageExtractor()
chart_skill = ChartGeneratorSkill(
    api_key=api_key,
    api_base=api_base if api_base else None,
    model=model if model else None
)

research_agent = ResearchAgent(
    api_key=api_key,
    api_base=api_base if api_base else None,
    model=model if model else None,
    literature_skill=literature_skill,
    image_skill=image_skill,
    pdf_extractor=pdf_extractor
)
writer_agent = WriterAgent(
    api_key=api_key,
    api_base=api_base if api_base else None,
    model=model if model else None,
    academic_rules_skill=academic_rules_skill,
    chart_skill=chart_skill,
    enable_images=True
)


# Pydantic models for request/response
class PaperRequest(BaseModel):
    title: str
    keywords: List[str]
    field: str
    length: str = "medium"  # short, medium, long
    citation_style: str = "apa"  # apa, mla, ieee, gbt7714
    language: str = "english"  # english, chinese


class PaperResponse(BaseModel):
    id: str
    title: str
    status: str
    sections: Optional[Dict[str, str]] = None
    created_at: str


class FormatRequest(BaseModel):
    paper_id: str
    style: str


@app.get("/")
def read_root():
    return {"message": "Academic Paper Assistant API", "version": "1.0.0"}


@app.get("/api/status")
def get_status():
    """Get API status and configuration."""
    return {
        "api_key_configured": bool(api_key),
        "model": model,
        "api_base": api_base if api_base else "default (anthropic)",
        "citation_styles": ["apa", "mla", "ieee", "gbt7714"],
        "length_options": ["short", "medium", "long"],
        "language_options": {
            "english": "English",
            "chinese": "中文"
        }
    }


@app.post("/api/papers", response_model=PaperResponse)
async def create_paper(request: PaperRequest, background_tasks: BackgroundTasks):
    """Create a new academic paper."""
    paper_id = f"paper_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Store initial status
    papers_db[paper_id] = {
        "id": paper_id,
        "title": request.title,
        "status": "generating",
        "sections": None,
        "created_at": datetime.now().isoformat(),
        "request": request.dict()
    }

    # Start generation in background
    background_tasks.add_task(generate_paper_task, paper_id, request)

    return PaperResponse(
        id=paper_id,
        title=request.title,
        status="generating",
        created_at=papers_db[paper_id]["created_at"]
    )


async def generate_paper_task(paper_id: str, request: PaperRequest):
    """Background task to generate paper."""
    try:
        # Step 1: Research
        research_result = await asyncio.to_thread(
            research_agent.analyze_topic,
            paper_title=request.title,
            keywords=request.keywords,
            research_field=request.field,
            language=request.language
        )

        papers_db[paper_id]["status"] = "writing"
        papers_db[paper_id]["research"] = research_result

        # Step 2: Writing
        paper_sections = await asyncio.to_thread(
            writer_agent.write_paper,
            research_info=research_result,
            length=request.length,
            citation_style=request.citation_style,
            language=request.language
        )

        papers_db[paper_id]["status"] = "completed"
        papers_db[paper_id]["sections"] = paper_sections

        # Save to file
        save_paper_to_file(paper_id, paper_sections, request)

    except Exception as e:
        papers_db[paper_id]["status"] = "failed"
        papers_db[paper_id]["error"] = str(e)


def save_paper_to_file(paper_id: str, sections: Dict[str, str], request: PaperRequest):
    """Save generated paper to file."""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    filename = f"{paper_id}_{request.citation_style}.md"
    filepath = output_dir / filename

    content = f"""# {sections.get('title', request.title)}

**Keywords:** {', '.join(request.keywords)}
**Field:** {request.field}
**Citation Style:** {request.citation_style.upper()}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Abstract

{sections.get('abstract', '')}

## Introduction

{sections.get('introduction', '')}

## Literature Review

{sections.get('literature_review', '')}

## Methodology

{sections.get('methodology', '')}

## Results

{sections.get('results', '')}

## Discussion

{sections.get('discussion', '')}

## Conclusion

{sections.get('conclusion', '')}

## References

{sections.get('references', '')}
"""

    filepath.write_text(content, encoding="utf-8")
    papers_db[paper_id]["filepath"] = str(filepath)


@app.get("/api/papers/{paper_id}")
def get_paper(paper_id: str):
    """Get paper by ID."""
    if paper_id not in papers_db:
        raise HTTPException(status_code=404, detail="Paper not found")

    return papers_db[paper_id]


@app.get("/api/papers")
def list_papers():
    """List all generated papers."""
    return list(papers_db.values())


@app.post("/api/papers/{paper_id}/format")
def format_paper(paper_id: str, request: FormatRequest):
    """Format paper with specific citation style."""
    if paper_id not in papers_db:
        raise HTTPException(status_code=404, detail="Paper not found")

    paper = papers_db[paper_id]
    if not paper.get("sections"):
        raise HTTPException(status_code=400, detail="Paper sections not available")

    # Reformat references
    sections = paper["sections"].copy()
    sections["references"] = writer_agent._format_references(
        paper.get("research", {}).get("literature", []),
        request.style,
        paper.get("research", {})
    )

    return {
        "paper_id": paper_id,
        "style": request.style,
        "sections": sections
    }


@app.get("/api/styles")
def get_citation_styles():
    """Get available citation styles with examples."""
    return {
        "apa": {
            "name": "APA 7th Edition",
            "description": "American Psychological Association style",
            "example": "Smith, J. (2023). Title of article. Journal Name, 45(2), 123-145."
        },
        "mla": {
            "name": "MLA 9th Edition",
            "description": "Modern Language Association style",
            "example": "Smith, John. \"Title of Article.\" Journal Name, vol. 45, no. 2, 2023, pp. 123-145."
        },
        "ieee": {
            "name": "IEEE",
            "description": "Institute of Electrical and Electronics Engineers style",
            "example": "[1] J. Smith, \"Title of article,\" Journal Name, vol. 45, no. 2, pp. 123-145, 2023."
        },
        "gbt7714": {
            "name": "GB/T7714",
            "description": "Chinese National Standard for bibliographic references",
            "example": "[1] 作者. 题名[J]. 期刊名, 2023, 45(2): 123-145."
        }
    }


@app.delete("/api/papers/{paper_id}")
def delete_paper(paper_id: str):
    """Delete a paper."""
    if paper_id not in papers_db:
        raise HTTPException(status_code=404, detail="Paper not found")

    del papers_db[paper_id]
    return {"message": "Paper deleted successfully"}


@app.get("/api/papers/{paper_id}/download/docx")
def download_paper_docx(paper_id: str):
    """
    Download paper as DOCX file.
    """
    if paper_id not in papers_db:
        raise HTTPException(status_code=404, detail="Paper not found")

    paper = papers_db[paper_id]

    if paper["status"] != "completed":
        raise HTTPException(status_code=400, detail="Paper not ready for download")

    if not paper.get("sections"):
        raise HTTPException(status_code=400, detail="Paper sections not available")

    try:
        # Generate DOCX
        generator = DocxGenerator()
        docx_path = generator.generate_from_paper_id(paper_id, papers_db)

        if not docx_path or not docx_path.exists():
            raise HTTPException(status_code=500, detail="Failed to generate DOCX file")

        # Store DOCX path
        papers_db[paper_id]["docx_path"] = str(docx_path)

        return FileResponse(
            path=docx_path,
            filename=f"{paper['title'][:50].replace(' ', '_')}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate DOCX: {str(e)}")


@app.get("/api/papers/{paper_id}/download/markdown")
def download_paper_markdown(paper_id: str):
    """
    Download paper as Markdown file.
    """
    if paper_id not in papers_db:
        raise HTTPException(status_code=404, detail="Paper not found")

    paper = papers_db[paper_id]

    if paper["status"] != "completed":
        raise HTTPException(status_code=400, detail="Paper not ready for download")

    if not paper.get("sections"):
        raise HTTPException(status_code=400, detail="Paper sections not available")

    try:
        request = paper.get("request", {})
        sections = paper["sections"]

        content = f"""# {sections.get('title', paper['title'])}

**Keywords:** {', '.join(request.get('keywords', []))}
**Field:** {request.get('field', 'N/A')}
**Citation Style:** {request.get('citation_style', 'apa').upper()}
**Language:** {request.get('language', 'english')}
**Generated:** {paper.get('created_at', '')}

---

## Abstract

{sections.get('abstract', '')}

## Introduction

{sections.get('introduction', '')}

## Literature Review

{sections.get('literature_review', '')}

## Methodology

{sections.get('methodology', '')}

## Results

{sections.get('results', '')}

## Discussion

{sections.get('discussion', '')}

## Conclusion

{sections.get('conclusion', '')}

## References

{sections.get('references', '')}
"""

        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        md_path = output_dir / f"{paper_id}.md"
        md_path.write_text(content, encoding="utf-8")

        return FileResponse(
            path=md_path,
            filename=f"{paper['title'][:50].replace(' ', '_')}.md",
            media_type="text/markdown"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Markdown: {str(e)}")


@app.get("/api/papers/{paper_id}/download/pdf")
def download_paper_pdf(paper_id: str):
    """
    Download paper as PDF file.
    """
    if paper_id not in papers_db:
        raise HTTPException(status_code=404, detail="Paper not found")

    paper = papers_db[paper_id]

    if paper["status"] != "completed":
        raise HTTPException(status_code=400, detail="Paper not ready for download")

    if not paper.get("sections"):
        raise HTTPException(status_code=400, detail="Paper sections not available")

    try:
        # Generate PDF
        generator = DocxGenerator()

        # Check if PDF already exists
        pdf_path = Path(f"output/{paper_id}.pdf")
        if pdf_path.exists():
            return FileResponse(
                path=pdf_path,
                filename=f"{paper['title'][:50].replace(' ', '_')}.pdf",
                media_type="application/pdf"
            )

        # Generate new PDF
        pdf_path = generator.generate_from_paper_id_pdf(paper_id, papers_db)

        if not pdf_path or not pdf_path.exists():
            raise HTTPException(status_code=500, detail="Failed to generate PDF file")

        return FileResponse(
            path=pdf_path,
            filename=f"{paper['title'][:50].replace(' ', '_')}.pdf",
            media_type="application/pdf"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
