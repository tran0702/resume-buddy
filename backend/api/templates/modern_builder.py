"""
Modern-style resume DOCX builder.
Clean single-column layout with SMALL CAPS section headers and blue accent underline.
Interface mirrors resume_builder.build() exactly:
  build(profile: dict, tailored: dict, options: dict) -> tuple[io.BytesIO, str]
"""
import io
from datetime import datetime
from typing import Optional

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


_BLUE_ACCENT = (122, 162, 247)   # Tokyo Night --color-blue


# ---- Helpers ----------------------------------------------------------------

def _set_font(run, size_pt: float, bold: bool = False, italic: bool = False,
              color: Optional[tuple] = None) -> None:
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)


def _set_margins(doc: Document) -> None:
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)


def _add_horizontal_rule(doc: Document) -> None:
    """Thin full-width separator after the contact line."""
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(4)
    para.paragraph_format.space_after = Pt(6)
    pPr = para._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '4')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), 'a9b1d6')
    pBdr.append(bottom)
    pPr.append(pBdr)


def _add_section_header(doc: Document, title: str) -> None:
    """SMALL CAPS bold header with a blue accent bottom border."""
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(8)
    para.paragraph_format.space_after = Pt(3)
    run = para.add_run(title.upper())
    _set_font(run, 10, bold=True, color=_BLUE_ACCENT)

    # Enable SMALL CAPS rendering via XML
    rPr = run._r.get_or_add_rPr()
    small_caps = OxmlElement('w:smallCaps')
    rPr.append(small_caps)

    # Blue bottom border (thicker than the Harvard rule)
    pPr = para._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '7aa2f7')
    pBdr.append(bottom)
    pPr.append(pBdr)


def _format_date(date_str: Optional[str]) -> str:
    if not date_str:
        return 'Present'
    try:
        dt = datetime.strptime(date_str, '%Y-%m')
        return dt.strftime('%b %Y')
    except ValueError:
        return date_str


def _add_employer_row(doc: Document, left_text: str, right_text: str) -> None:
    """Company/institution left, date right — same right-aligned tab stop as Harvard."""
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(5)
    para.paragraph_format.space_after = Pt(1)

    pPr = para._p.get_or_add_pPr()
    tabs = OxmlElement('w:tabs')
    tab = OxmlElement('w:tab')
    tab.set(qn('w:val'), 'right')
    tab.set(qn('w:pos'), '9360')
    tabs.append(tab)
    pPr.append(tabs)

    run_left = para.add_run(left_text)
    _set_font(run_left, 10, bold=True)
    if right_text:
        para.add_run('\t')
        run_right = para.add_run(right_text)
        _set_font(run_right, 10, bold=True)


def _add_title_line(doc: Document, text: str) -> None:
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.space_after = Pt(1)
    run = para.add_run(text)
    _set_font(run, 10, italic=True)


def _add_bullet(doc: Document, text: str) -> None:
    para = doc.add_paragraph(style='List Bullet')
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.space_after = Pt(1)
    para.paragraph_format.left_indent = Inches(0.2)
    run = para.add_run(text)
    _set_font(run, 10)


def _add_body_para(doc: Document, text: str, space_before: float = 2) -> None:
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(space_before)
    para.paragraph_format.space_after = Pt(1)
    run = para.add_run(text)
    _set_font(run, 10)


# ---- Preview ----------------------------------------------------------------

def _build_preview(profile: dict, tailored: dict) -> str:
    lines = []
    contact = profile.get('contact', {})
    lines.append(contact.get('name', ''))
    contact_parts = [p for p in [
        contact.get('email'), contact.get('phone'),
        contact.get('location'), contact.get('linkedin')
    ] if p]
    if contact_parts:
        lines.append(' · '.join(contact_parts))
    lines.append('')

    if profile.get('summary'):
        lines.append('SUMMARY')
        lines.append(profile['summary'])
        lines.append('')

    bullet_map: dict[str, list[str]] = {}
    for te in tailored.get('tailored_experience', []):
        key = f"{te.get('company', '')}|{te.get('title', '')}"
        bullet_map[key] = te.get('tailored_bullets', [])

    if profile.get('work_experience'):
        lines.append('EXPERIENCE')
        for exp in profile['work_experience']:
            date_str = (
                f"{_format_date(exp.get('start_date'))} – "
                f"{_format_date(exp.get('end_date'))}"
            )
            lines.append(f"  {exp.get('company', '')}  {date_str}")
            lines.append(f"  {exp.get('title', '')}")
            key = f"{exp.get('company', '')}|{exp.get('title', '')}"
            for b in bullet_map.get(key, exp.get('bullets', [])):
                lines.append(f"  • {b}")
            lines.append('')

    if profile.get('education'):
        lines.append('EDUCATION')
        for edu in profile['education']:
            lines.append(
                f"  {edu.get('institution', '')}  "
                f"{_format_date(edu.get('graduation_date'))}"
            )
            lines.append(f"  {edu.get('degree', '')} in {edu.get('field_of_study', '')}")
            lines.append('')

    if profile.get('skills'):
        lines.append('SKILLS')
        lines.append('  ' + ', '.join(profile['skills']))
        lines.append('')

    return '\n'.join(lines)


# ---- Main build function ----------------------------------------------------

def build(
    profile: dict,
    tailored: dict,
    options: dict
) -> tuple[io.BytesIO, str]:
    """
    Build a Modern-style resume DOCX.
    Interface is identical to resume_builder.build().
    """
    doc = Document()
    _set_margins(doc)

    normal_style = doc.styles['Normal']
    normal_style.paragraph_format.space_before = Pt(0)
    normal_style.paragraph_format.space_after = Pt(0)

    contact = profile.get('contact', {})

    # --- Name ---
    name_para = doc.add_paragraph()
    name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name_para.paragraph_format.space_before = Pt(0)
    name_para.paragraph_format.space_after = Pt(3)
    name_run = name_para.add_run(contact.get('name', 'Full Name'))
    _set_font(name_run, 22, bold=True)

    # --- Contact line (· separated, centered) ---
    contact_parts = [p for p in [
        contact.get('email'), contact.get('phone'),
        contact.get('location'), contact.get('linkedin')
    ] if p]
    if contact_parts:
        contact_para = doc.add_paragraph()
        contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact_para.paragraph_format.space_before = Pt(0)
        contact_para.paragraph_format.space_after = Pt(4)
        contact_run = contact_para.add_run(' · '.join(contact_parts))
        _set_font(contact_run, 10)

    # --- Horizontal rule ---
    _add_horizontal_rule(doc)

    # --- Summary ---
    if profile.get('summary'):
        _add_section_header(doc, 'Summary')
        _add_body_para(doc, profile['summary'])

    # --- Experience ---
    work_exp = profile.get('work_experience', [])
    if work_exp:
        _add_section_header(doc, 'Experience')
        bullet_map: dict[str, list[str]] = {}
        for te in tailored.get('tailored_experience', []):
            key = f"{te.get('company', '')}|{te.get('title', '')}"
            bullet_map[key] = te.get('tailored_bullets', [])

        for exp in work_exp:
            date_str = (
                f"{_format_date(exp.get('start_date'))} – "
                f"{_format_date(exp.get('end_date'))}"
            )
            _add_employer_row(doc, exp.get('company', ''), date_str)
            _add_title_line(doc, exp.get('title', ''))
            key = f"{exp.get('company', '')}|{exp.get('title', '')}"
            for b in bullet_map.get(key, exp.get('bullets', [])):
                _add_bullet(doc, b)

    # --- Education ---
    if profile.get('education'):
        _add_section_header(doc, 'Education')
        for edu in profile['education']:
            _add_employer_row(
                doc,
                edu.get('institution', ''),
                _format_date(edu.get('graduation_date'))
            )
            degree_line = edu.get('degree', '')
            if edu.get('field_of_study'):
                degree_line += f" in {edu['field_of_study']}"
            if edu.get('gpa'):
                degree_line += f"  GPA: {edu['gpa']}"
            _add_title_line(doc, degree_line)
            for honor in edu.get('honors', []):
                _add_bullet(doc, honor)

    # --- Skills ---
    if options.get('include_skills', True) and profile.get('skills'):
        _add_section_header(doc, 'Skills')
        _add_body_para(doc, ', '.join(profile['skills']))

    # --- Projects ---
    if options.get('include_projects', False) and profile.get('projects'):
        _add_section_header(doc, 'Projects')
        for proj in profile['projects']:
            name_line = proj.get('name', '')
            if proj.get('url'):
                name_line += f"  {proj['url']}"
            _add_employer_row(doc, name_line, '')
            if proj.get('description'):
                _add_body_para(doc, proj['description'])
            if proj.get('technologies'):
                _add_body_para(doc, 'Technologies: ' + ', '.join(proj['technologies']))

    # --- Certifications ---
    if options.get('include_certifications', True) and profile.get('certifications'):
        _add_section_header(doc, 'Certifications')
        for cert in profile['certifications']:
            _add_bullet(doc, cert)

    # --- Volunteer ---
    if options.get('include_volunteer', False) and profile.get('volunteer'):
        _add_section_header(doc, 'Volunteer')
        for vol in profile['volunteer']:
            _add_bullet(doc, vol)

    # --- Languages ---
    if profile.get('languages'):
        _add_section_header(doc, 'Languages')
        _add_body_para(doc, ', '.join(profile['languages']))

    # --- Page limit heuristic ---
    char_count = sum(len(p.text) for p in doc.paragraphs)
    if options.get('max_pages', 2) == 1 and char_count > 3000:
        tailored.setdefault('tailoring_notes', []).append(
            f'Warning: estimated content (~{char_count} chars) may exceed 1 page.'
        )
    elif char_count > 5500:
        tailored.setdefault('tailoring_notes', []).append(
            f'Warning: estimated content (~{char_count} chars) may exceed 2 pages.'
        )

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)

    preview_text = _build_preview(profile, tailored)
    return buf, preview_text
