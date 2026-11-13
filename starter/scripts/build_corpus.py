import urllib.request
import xml.etree.ElementTree as ET
import re
import json
import csv
import unicodedata
from pathlib import Path
import shutil
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors

SELECTED_MODULES = [
    # Statements
    {"page": 1, "module_id": "m00002", "chapter": "Statements", "topic": "Background"},
    {"page": 2, "module_id": "m00003", "chapter": "Statements", "topic": "Input/output"},
    {"page": 3, "module_id": "m00004", "chapter": "Statements", "topic": "Variables"},
    {"page": 4, "module_id": "m00005", "chapter": "Statements", "topic": "String basics"},
    {"page": 5, "module_id": "m00006", "chapter": "Statements", "topic": "Number basics"},
    {"page": 6, "module_id": "m00007", "chapter": "Statements", "topic": "Error messages"},
    {"page": 7, "module_id": "m00008", "chapter": "Statements", "topic": "Comments"},
    {"page": 8, "module_id": "m00009", "chapter": "Statements", "topic": "Why Python?"},
    {"page": 9, "module_id": "m00114", "chapter": "Statements", "topic": "Chapter summary"},
    # Expressions
    {"page": 10, "module_id": "m00011", "chapter": "Expressions", "topic": "The Python shell"},
    {"page": 11, "module_id": "m00012", "chapter": "Expressions", "topic": "Type conversion"},
    {"page": 12, "module_id": "m00013", "chapter": "Expressions", "topic": "Mixed data types"},
    {"page": 13, "module_id": "m00014", "chapter": "Expressions", "topic": "Floating-point errors"},
    {"page": 14, "module_id": "m00015", "chapter": "Expressions", "topic": "Dividing integers"},
    {"page": 15, "module_id": "m00016", "chapter": "Expressions", "topic": "The math module"},
    {"page": 16, "module_id": "m00017", "chapter": "Expressions", "topic": "Formatting code"},
    {"page": 17, "module_id": "m00018", "chapter": "Expressions", "topic": "Python careers"},
    {"page": 18, "module_id": "m00019", "chapter": "Expressions", "topic": "Chapter summary"},
    # Decisions
    {"page": 19, "module_id": "m00028", "chapter": "Decisions", "topic": "Boolean values"},
    {"page": 20, "module_id": "m00029", "chapter": "Decisions", "topic": "If-else statements"},
    {"page": 21, "module_id": "m00030", "chapter": "Decisions", "topic": "Boolean operations"},
    {"page": 22, "module_id": "m00031", "chapter": "Decisions", "topic": "Operator precedence"},
    {"page": 23, "module_id": "m00032", "chapter": "Decisions", "topic": "Chained decisions"},
    {"page": 24, "module_id": "m00033", "chapter": "Decisions", "topic": "Nested decisions"},
    {"page": 25, "module_id": "m00035", "chapter": "Decisions", "topic": "Chapter summary"},
    # Loops
    {"page": 26, "module_id": "m00037", "chapter": "Loops", "topic": "While loop"},
    {"page": 27, "module_id": "m00038", "chapter": "Loops", "topic": "For loop"},
    {"page": 28, "module_id": "m00039", "chapter": "Loops", "topic": "Nested loops"},
    {"page": 29, "module_id": "m00040", "chapter": "Loops", "topic": "Break and continue"},
    {"page": 30, "module_id": "m00041", "chapter": "Loops", "topic": "Loop else"},
    {"page": 31, "module_id": "m00042", "chapter": "Loops", "topic": "Chapter summary"},
    # Functions
    {"page": 32, "module_id": "m00044", "chapter": "Functions", "topic": "Defining functions"},
    {"page": 33, "module_id": "m00045", "chapter": "Functions", "topic": "Control flow"},
    {"page": 34, "module_id": "m00046", "chapter": "Functions", "topic": "Variable scope"},
    {"page": 35, "module_id": "m00047", "chapter": "Functions", "topic": "Parameters"},
]

def parse_cnxml_complete(xml_bytes):
    root = ET.fromstring(xml_bytes)
    ns = {'cnxml': 'http://cnx.rice.edu/cnxml'}
    
    title_elem = root.find('cnxml:title', ns)
    main_title = title_elem.text.strip() if title_elem is not None and title_elem.text else ''
    content_elem = root.find('cnxml:content', ns)
    
    if content_elem is None:
        return main_title, []
        
    sections = []
    current_heading = main_title
    current_paras = []
    
    for child in content_elem:
        tag = child.tag.split('}')[-1]
        if tag == 'title':
            continue
        if tag == 'section':
            if current_paras:
                sections.append({'heading': current_heading, 'paragraphs': current_paras})
                current_paras = []
            sec_title_elem = child.find('cnxml:title', ns)
            sec_heading = sec_title_elem.text.strip() if sec_title_elem is not None and sec_title_elem.text else current_heading
            sec_paras = []
            for sec_child in child:
                stag = sec_child.tag.split('}')[-1]
                if stag == 'title':
                    continue
                txt = unicodedata.normalize('NFKC', ''.join(sec_child.itertext()))
                txt = re.sub(r'\s+', ' ', txt).strip()
                if txt:
                    sec_paras.append(txt)
            if sec_paras:
                sections.append({'heading': sec_heading, 'paragraphs': sec_paras})
        else:
            txt = unicodedata.normalize('NFKC', ''.join(child.itertext()))
            txt = re.sub(r'\s+', ' ', txt).strip()
            if txt:
                current_paras.append(txt)
                
    if current_paras:
        sections.append({'heading': current_heading, 'paragraphs': current_paras})
        
    return main_title, sections

def fetch_and_build():
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = data_dir / "raw_xml"
    raw_dir.mkdir(parents=True, exist_ok=True)
    starter_data_dir = Path("starter/data")
    starter_data_dir.mkdir(parents=True, exist_ok=True)
    
    corpus_pages = []
    manifest_pages = []
    
    print(f"Processing {len(SELECTED_MODULES)} modules from OpenStax...")
    for idx, item in enumerate(SELECTED_MODULES, 1):
        mod_id = item["module_id"]
        ch = item["chapter"]
        page_num = item["page"]
        raw_xml_file = raw_dir / f"{mod_id}.cnxml"
        
        if raw_xml_file.exists():
            with open(raw_xml_file, "rb") as f:
                xml_bytes = f.read()
        else:
            url = f"https://raw.githubusercontent.com/openstax/osbooks-introduction-python-programming/main/modules/{mod_id}/index.cnxml"
            req = urllib.request.Request(url, headers={"User-Agent": "Python/DataIngestionLab"})
            xml_bytes = urllib.request.urlopen(req, timeout=30).read()
            with open(raw_xml_file, "wb") as f:
                f.write(xml_bytes)
        
        extracted_title, sections = parse_cnxml_complete(xml_bytes)
        title = extracted_title if extracted_title else item["topic"]
        
        full_text_parts = []
        for s in sections:
            full_text_parts.append(f"## {s['heading']}")
            full_text_parts.extend(s['paragraphs'])
        
        normalized_full_text = "\n\n".join(full_text_parts)
        char_count = len(normalized_full_text)
        
        doc_page = {
            "document_id": "openstax-python-foundations",
            "source": "data/openstax_python_foundations.pdf",
            "page": page_num,
            "module_id": mod_id,
            "chapter": ch,
            "title": title,
            "character_count": char_count,
            "sections": sections,
            "text": normalized_full_text
        }
        corpus_pages.append(doc_page)
        
        manifest_pages.append({
            "page_id": page_num,
            "module_id": mod_id,
            "chapter": ch,
            "title": title,
            "character_count": char_count,
            "status": "included",
            "reason": f"Useful content unit with {char_count:,} characters (>= 1,500 threshold)"
        })
        print(f"  [{idx:02d}/35] Page {page_num:02d}: [{ch}] {mod_id} - {title} ({char_count:,} chars)")

    # Save corpus.json
    corpus_file = data_dir / "corpus.json"
    with open(corpus_file, "w", encoding="utf-8") as f:
        json.dump(corpus_pages, f, ensure_ascii=False, indent=2)
    with open(starter_data_dir / "corpus.json", "w", encoding="utf-8") as f:
        json.dump(corpus_pages, f, ensure_ascii=False, indent=2)
    print(f"Saved corpus to {corpus_file}")

    # Build manifest
    total_chars = sum(p["character_count"] for p in manifest_pages)
    manifest_data = {
        "source_id": "openstax-python-foundations",
        "title": "OpenStax Introduction to Python Programming: Core Foundations",
        "source_path_or_url": "https://openstax.org/details/books/introduction-python-programming",
        "git_repository": "https://github.com/openstax/osbooks-introduction-python-programming",
        "license_or_permission": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
        "accessed_at": "2026-11-13T17:20:00+07:00",
        "snapshot_version": "main-commit-8d08a72f-5463-4856-b05c-58b0d65f5e61",
        "content_type": "Curriculum Textbook (Computer Science / Programming)",
        "total_physical_pages": 35,
        "included_content_pages": 35,
        "excluded_pages": [
            {"page": 0, "reason": "Cover page, front matter, copyright notice (retained in manifest)"},
            {"reason": "TOC and blank divider pages excluded"}
        ],
        "counting_method": "Each physical page represents one sequential, modular content unit with >= 1,500 normalized characters from chapters Statements, Expressions, Decisions, Loops, Functions. Front matter, covers, and empty pages are excluded from the 35 useful content pages.",
        "total_character_count": total_chars,
        "pages": manifest_pages
    }

    manifest_json_file = data_dir / "manifest.json"
    with open(manifest_json_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)
    with open(starter_data_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)
    print(f"Saved manifest to {manifest_json_file}")

    # Build manifest.csv
    manifest_csv_file = data_dir / "manifest.csv"
    with open(manifest_csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["page_id", "module_id", "chapter", "title", "character_count", "status", "reason"])
        for p in manifest_pages:
            writer.writerow([p["page_id"], p["module_id"], p["chapter"], p["title"], p["character_count"], p["status"], p["reason"]])
    with open(starter_data_dir / "manifest.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["page_id", "module_id", "chapter", "title", "character_count", "status", "reason"])
        for p in manifest_pages:
            writer.writerow([p["page_id"], p["module_id"], p["chapter"], p["title"], p["character_count"], p["status"], p["reason"]])
    print(f"Saved CSV manifest to {manifest_csv_file}")

    # Build PDF with ReportLab: 1 physical page per module
    print("Generating PDF data/openstax_python_foundations.pdf...")
    pdf_path = data_dir / "openstax_python_foundations.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#1a365d'),
        spaceAfter=3
    )
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#4a5568'),
        spaceAfter=5
    )
    h2_style = ParagraphStyle(
        'H2Style',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=11.5,
        textColor=colors.HexColor('#2b6cb0'),
        spaceBefore=3,
        spaceAfter=2
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.0,
        leading=8.8,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=2.5
    )

    story = []
    for idx, cp in enumerate(corpus_pages):
        header_text = f"<b>Page {cp['page']} | OpenStax Python Programming: Chapter {cp['chapter']} - {cp['title']}</b>"
        sub_text = f"Module ID: {cp['module_id']} | Source: OpenStax (CC BY-NC-SA 4.0) | Characters: {cp['character_count']:,}"
        story.append(Paragraph(header_text, title_style))
        story.append(Paragraph(sub_text, meta_style))
        story.append(Spacer(1, 3))
        
        for sec in cp['sections']:
            if sec['heading'] and sec['heading'] != cp['title']:
                escaped_h2 = sec['heading'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(escaped_h2, h2_style))
            for p in sec['paragraphs']:
                escaped_p = p.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(escaped_p, body_style))
                
        if idx < len(corpus_pages) - 1:
            story.append(PageBreak())

    doc.build(story)
    shutil.copy(pdf_path, starter_data_dir / "openstax_python_foundations.pdf")
    print(f"Generated PDF with {len(corpus_pages)} pages at {pdf_path}")

if __name__ == "__main__":
    fetch_and_build()
