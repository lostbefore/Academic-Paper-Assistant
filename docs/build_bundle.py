"""Build a single print-ready HTML (and then a PDF via headless Edge).

Usage:
    python docs/build_bundle.py
    msedge --headless=new --print-to-pdf=... file:///.../docs-bundle.html
"""

from __future__ import annotations

import html
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

ORDER = [
    ("README.md", "文档集说明"),
    ("01-需求分析与项目概述.md", "需求分析与项目概述"),
    ("02-系统架构设计.md", "系统架构设计"),
    ("03-数据库设计.md", "数据库设计"),
    ("04-接口设计.md", "接口设计"),
    ("05-生成流水线设计.md", "生成流水线设计"),
    ("06-关键模块设计.md", "关键模块设计"),
    ("07-前端设计.md", "前端设计"),
    ("08-测试方案与测试记录.md", "测试方案与测试记录"),
    ("09-部署与运维.md", "部署与运维"),
    ("10-版本演进与变更记录.md", "版本演进与变更记录"),
    ("11-学术诚信与使用边界.md", "学术诚信与使用边界"),
    ("12-开发过程记录.md", "开发过程记录"),
    ("appendix/A-代码统计.md", "附录 A 代码与文件统计"),
    ("appendix/B-接口清单.md", "附录 B 接口清单"),
    ("appendix/C-数据库结构.md", "附录 C 数据库结构"),
    ("appendix/D-提交历史.md", "附录 D 提交历史"),
    ("appendix/F-文档清单.md", "附录 F 文档清单"),
]

CSS = """
@page { size: A4; margin: 20mm 18mm 18mm 18mm; }
* { box-sizing: border-box; }
body { font-family: "Microsoft YaHei", "PingFang SC", "SimSun", sans-serif;
       font-size: 10.5pt; line-height: 1.75; color: #1a1a1a; margin: 0; }
.cover { height: 245mm; display: flex; flex-direction: column; justify-content: center;
         page-break-after: always; text-align: center; }
.cover .line { width: 60mm; height: 3px; background: #1d4ed8; margin: 18mm auto; }
.cover h1 { font-size: 30pt; margin: 0 0 6mm; letter-spacing: 2px; color: #0f172a; }
.cover h2 { font-size: 15pt; font-weight: normal; color: #475569; margin: 0; }
.cover .meta { margin-top: 30mm; font-size: 11pt; color: #334155; line-height: 2.2; }
.cover .foot { margin-top: 40mm; font-size: 9pt; color: #94a3b8; }
.doc { page-break-before: always; }
.doc h1 { font-size: 20pt; color: #0f172a; border-bottom: 2px solid #1d4ed8;
          padding-bottom: 3mm; margin: 0 0 6mm; }
.doc h2 { font-size: 14pt; color: #1e3a8a; margin: 8mm 0 3mm; }
.doc h3 { font-size: 12pt; color: #1e293b; margin: 6mm 0 2mm; }
p { margin: 0 0 3mm; text-align: justify; }
table { width: 100%; border-collapse: collapse; margin: 4mm 0 5mm; font-size: 9.5pt; }
th, td { border: 1px solid #cbd5e1; padding: 1.6mm 2.2mm; vertical-align: top; }
th { background: #eff6ff; font-weight: 600; text-align: left; }
tr:nth-child(even) td { background: #f8fafc; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9pt;
       background: #f1f5f9; padding: 0.4mm 1.2mm; border-radius: 2px; }
pre { background: #0f172a; color: #e2e8f0; padding: 3mm 4mm; border-radius: 2mm;
      overflow-x: auto; font-size: 8.5pt; line-height: 1.5; page-break-inside: avoid; }
pre code { background: transparent; color: inherit; padding: 0; }
blockquote { margin: 3mm 0; padding: 2mm 4mm; border-left: 3px solid #93c5fd;
             background: #f8fafc; color: #334155; }
ul, ol { margin: 2mm 0 3mm; padding-left: 7mm; }
li { margin: 0.8mm 0; }
img { max-width: 100%; border: 1px solid #e2e8f0; border-radius: 2mm; margin: 2mm 0; }
hr { border: none; border-top: 1px solid #e2e8f0; margin: 6mm 0; }
"""


def render(md_text: str) -> str:
    text = md_text
    # Resolve images for file:// rendering.
    text = re.sub(r"\]\((images/[^)]+)\)", lambda m: "](file:///" + str((DOCS / m.group(1)).as_posix()) + ")", text)
    return markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "sane_lists", "nl2br"],
    )


def main() -> None:
    parts = []
    for rel, title in ORDER:
        path = DOCS / rel
        if not path.exists():
            continue
        body = render(path.read_text(encoding="utf-8"))
        parts.append(f'<section class="doc">\n{body}\n</section>')

    report = DOCS / "appendix" / "test-report.txt"
    if report.exists():
        raw = report.read_text(encoding="utf-8", errors="ignore")
        parts.append(
            '<section class="doc"><h1>附录 E 测试执行日志</h1>'
            "<p>以下为 <code>pytest -v</code> 的原始输出（节选）。</p><pre>"
            + html.escape(raw[-12000:])
            + "</pre></section>"
        )

    document = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>学术论文助手 · 设计与开发文档集</title>
<style>{CSS}</style></head><body>
<div class="cover">
  <h2>Academic Paper Assistant</h2>
  <div class="line"></div>
  <h1>学术论文助手</h1>
  <h2>系统设计与开发文档集</h2>
  <div class="meta">
    文档版本：V2.0<br>
    对应系统版本：v2.0.0<br>
    设计定稿：2026 年 6 月<br>
    文档校订：2026 年 11 月
  </div>
  <div class="foot">本文件由仓库内 Markdown 文档自动汇编生成，内容与 docs/ 目录一致</div>
</div>
{''.join(parts)}
</body></html>"""

    out = DOCS / "docs-bundle.html"
    out.write_text(document, encoding="utf-8")
    print("wrote", out, len(document), "chars")
    print(
        "render: msedge --headless=new --disable-gpu --no-pdf-header-footer "
        f'--print-to-pdf="{DOCS / "学术论文助手-设计与开发文档集.pdf"}" "file:///{out.as_posix()}"'
    )


if __name__ == "__main__":
    main()
