"""Assemble the single-file submission PDF in stages.

Chromium cannot be spawned reliably from Python in this environment (the
process hangs), so printing is orchestrated by PowerShell:

    python build_submission_pdf.py render1            # -> _pass1.html
    msedge --print-to-pdf=_pass1.pdf file:///.../_pass1.html
    python build_submission_pdf.py measure _pass1.pdf # -> pages.json on stdout
    python build_submission_pdf.py render2 "<json>"   # -> _pass2.html
    msedge --print-to-pdf=_pass2.pdf file:///.../_pass2.html
    python build_submission_pdf.py stamp _pass2.pdf   # -> final pdf
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

from build_bundle import CSS, DOCS, ORDER, render

FINAL = DOCS / "学术论文助手-自主设计过程文档.pdf"
HTML1 = DOCS / "_pass1.html"
HTML2 = DOCS / "_pass2.html"

SECTIONS = [
    ("00", "开发过程记录"),
    ("01", "需求分析与项目概述"),
    ("02", "系统架构设计"),
    ("03", "数据库设计"),
    ("04", "接口设计"),
    ("05", "生成流水线设计"),
    ("06", "关键模块设计"),
    ("07", "前端设计"),
    ("08", "测试方案与测试记录"),
    ("09", "部署与运维"),
    ("10", "版本演进与变更记录"),
    ("11", "学术诚信与使用边界"),
    ("附录 A", "代码与文件统计"),
    ("附录 B", "HTTP 接口清单"),
    ("附录 C", "数据库结构"),
    ("附录 D", "版本库提交历史"),
    ("附录 E", "测试执行日志"),
    ("附录 F", "文档文件清单"),
    ("附录 G", "2026-11-16 整理与部署记录"),
]


def collect_sections() -> list[tuple[str, str]]:
    rendered: list[tuple[str, str]] = []
    for rel, _title in ORDER:
        if rel in {"appendix/F-文档清单.md", "appendix/G-整理与部署记录.md"}:
            continue  # appended after the test log so the appendix order stays A..F
        path = DOCS / rel
        if path.exists():
            rendered.append((rel, render(path.read_text(encoding="utf-8"))))

    report = DOCS / "appendix" / "test-report.txt"
    if report.exists():
        raw = report.read_text(encoding="utf-8", errors="ignore")[-14000:]
        body = (
            "<h1>附录 E · 测试执行日志</h1>"
            "<p>以下为 <code>pytest -v</code> 的原始输出，用于核对第 08 章测试结论。</p>"
            "<pre>"
            + raw.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            + "</pre>"
        )
        rendered.append(("appendix/E", body))

    inventory = DOCS / "appendix" / "F-文档清单.md"
    if inventory.exists():
        rendered.append(("appendix/F", render(inventory.read_text(encoding="utf-8"))))

    deploy = DOCS / "appendix" / "G-整理与部署记录.md"
    if deploy.exists():
        rendered.append(("appendix/G", render(deploy.read_text(encoding="utf-8"))))
    return rendered


def toc_html(entries: list[tuple[str, str, int]]) -> str:
    rows = "\n".join(
        f'<div class="toc-row"><span class="toc-num">{num}</span>'
        f'<span class="toc-title">{title}</span>'
        f'<span class="toc-dots"></span><span class="toc-page">{page}</span></div>'
        for num, title, page in entries
    )
    return f"""<section class="doc toc">
<h1>目　录</h1>
<div class="toc-list">{rows}</div>
<p class="toc-note">页码为本 PDF 的实际页码；各章标题与正文一一对应。</p>
</section>"""


def page_html(sections: list[tuple[str, str]], toc: str = "") -> str:
    body = "\n".join(f'<section class="doc">\n{html}\n</section>' for _rel, html in sections)
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>学术论文助手 · 自主设计过程文档</title><style>{CSS}
.toc-list {{ margin-top: 6mm; }}
.toc-row {{ display: flex; align-items: baseline; font-size: 10.5pt; margin: 0 0 3.2mm; }}
.toc-num {{ width: 16mm; color: #1d4ed8; }}
.toc-title {{ white-space: nowrap; }}
.toc-dots {{ flex: 1; border-bottom: 1px dotted #94a3b8; margin: 0 2mm; }}
.toc-page {{ width: 10mm; text-align: right; }}
.toc-note {{ margin-top: 10mm; font-size: 9pt; color: #64748b; }}
</style></head><body>
<div class="cover">
  <h2>Academic Paper Assistant</h2>
  <div class="line"></div>
  <h1>学术论文助手</h1>
  <h2>自主设计过程文档</h2>
  <div class="meta">
    文档版本：V2.0<br>
    对应系统版本：v2.0.0<br>
    设计定稿：2026 年 6 月<br>
    文档校订：2026 年 11 月
  </div>
  <div class="foot">本文件由仓库 docs/ 目录下的文档自动汇编，内容与源码、测试记录一一对应</div>
</div>
{toc}
{body}
</body></html>"""


def measure(pdf_path: Path) -> list[list]:
    reader = PdfReader(str(pdf_path))
    texts = [(p.extract_text() or "").replace("\u3000", " ") for p in reader.pages]
    result = []
    for num, title in SECTIONS:
        needle = f"{num} · {title}"
        page_no = 0
        for index, text in enumerate(texts, start=1):
            if needle in re.sub(r"\s+", " ", text):
                page_no = index
                break
        result.append([num, title, page_no])
    return result


def stamp(pdf_path: Path) -> int:
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        font = "STSong-Light"
    except Exception:  # pragma: no cover
        font = "Helvetica"

    reader = PdfReader(str(pdf_path))
    total = len(reader.pages)
    writer = PdfWriter()
    for index, page in enumerate(reader.pages):
        writer.add_page(page)
        if index > 0:
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            c.setFont(font, 8)
            c.setFillColorRGB(0.45, 0.45, 0.45)
            c.drawRightString(A4[0] - 51, A4[1] - 34, "学术论文助手 · 自主设计过程文档")
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.setLineWidth(0.4)
            c.line(51, A4[1] - 40, A4[0] - 51, A4[1] - 40)
            c.setFont(font, 9)
            c.drawCentredString(A4[0] / 2, 30, f"第 {index + 1} 页 / 共 {total} 页")
            c.save()
            buffer.seek(0)
            writer.pages[-1].merge_page(PdfReader(buffer).pages[0])
    with FINAL.open("wb") as handle:
        writer.write(handle)
    return total


def main(argv: list[str]) -> None:
    stage = argv[1] if len(argv) > 1 else ""
    sections = collect_sections()

    if stage == "render1":
        HTML1.write_text(page_html(sections), encoding="utf-8")
        print(HTML1)
        return

    if stage == "measure":
        pages = measure(Path(argv[2]))
        (DOCS / "pages.json").write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
        print("measured", len(pages), "sections")
        return

    if stage == "render2":
        pages = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
        entries = [(num, title, page + 1 if page else 0) for num, title, page in pages]
        HTML2.write_text(page_html(sections, toc_html(entries)), encoding="utf-8")
        missing = [num for num, _t, page in entries if page == 0]
        print(HTML2)
        if missing:
            print("missing:", missing, file=sys.stderr)
        return

    if stage == "stamp":
        total = stamp(Path(argv[2]))
        print(f"{FINAL} pages={total}")
        return

    raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
