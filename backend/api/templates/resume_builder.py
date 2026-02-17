"""
Harvard-style resume DOCX builder.
Accepts a MasterProfile dict + tailored bullets dict + generation options.
Returns a tuple of (io.BytesIO DOCX, preview_text str).

Harvard style conventions used:
- Name: 18pt bold, centered
- Contact line: 11pt, centered
- Section headers: 11pt ALL CAPS bold + bottom border (thin rule)
- Employer line: company bold-left, date bold-right (tab stop)
- Title line: italic, indented
- Bullets: 10.5pt, hanging indent, solid square bullet character
- Body text: 10.5pt
"""
import copy
import io
import math
from datetime import datetime
from typing import Optional

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ---- Page-limit constants ---------------------------------------------------
# Letter paper, 1-inch margins → 6.5" × 9" printable area.
# 10.5pt font with ~14pt leading → ~46 body lines per page.
_LINES_PER_PAGE = 46
_CHARS_PER_LINE = 90   # approx chars that fit in 6.5" at 10.5pt


# ---- Helpers ----------------------------------------------------------------

def _set_font(run, size_pt: float, bold: bool = False, italic: bool = False,
              color: Optional[tuple] = None) -> None:
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)


def _add_section_header(doc: Document, title: str) -> None:
    """Add an ALL-CAPS bold section header with a bottom border rule."""
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(8)
    para.paragraph_format.space_after = Pt(2)
    run = para.add_run(title.upper())
    _set_font(run, 11, bold=True)

    # Add a bottom border to the paragraph (thin horizontal rule)
    pPr = para._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '4')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '2d3149')
    pBdr.append(bottom)
    pPr.append(pBdr)


def _format_date(date_str: Optional[str]) -> str:
    """Convert YYYY-MM to 'Mon YYYY'. Returns 'Present' for None."""
    if not date_str:
        return 'Present'
    try:
        dt = datetime.strptime(date_str, '%Y-%m')
        return dt.strftime('%b %Y')
    except ValueError:
        return date_str


def _add_employer_row(doc: Document, company: str, date_str: str) -> None:
    """Add 'Company Name [tab] Date Range' with right-aligned date."""
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(6)
    para.paragraph_format.space_after = Pt(1)

    # Tab stop at right margin
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    pPr = para._p.get_or_add_pPr()
    tabs = OxmlElement('w:tabs')
    tab = OxmlElement('w:tab')
    tab.set(qn('w:val'), 'right')
    tab.set(qn('w:pos'), '9360')   # 6.5 inches in twips (1440 twips/inch)
    tabs.append(tab)
    pPr.append(tabs)

    run_co = para.add_run(company)
    _set_font(run_co, 10.5, bold=True)

    run_tab = para.add_run('\t')
    _set_font(run_tab, 10.5)

    run_dt = para.add_run(date_str)
    _set_font(run_dt, 10.5, bold=True)


def _add_title_line(doc: Document, title: str) -> None:
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.space_after = Pt(1)
    run = para.add_run(title)
    _set_font(run, 10.5, italic=True)


def _add_bullet(doc: Document, text: str) -> None:
    para = doc.add_paragraph(style='List Bullet')
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.space_after = Pt(1)
    para.paragraph_format.left_indent = Inches(0.25)
    run = para.add_run(text)
    _set_font(run, 10.5)


def _add_body_para(doc: Document, text: str, space_before: float = 2) -> None:
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(space_before)
    para.paragraph_format.space_after = Pt(1)
    run = para.add_run(text)
    _set_font(run, 10.5)


# ---- Page margins -----------------------------------------------------------

def _set_margins(doc: Document) -> None:
    """Set 1-inch margins on all sides."""
    from docx.shared import Inches
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)


# ---- Preview text builder ---------------------------------------------------

def _build_preview(profile: dict, tailored: dict) -> str:
    """Build a plain-text representation of the resume for in-app preview."""
    lines = []
    contact = profile.get('contact', {})
    lines.append(contact.get('name', ''))
    contact_parts = [p for p in [
        contact.get('email'), contact.get('phone'),
        contact.get('location'), contact.get('linkedin')
    ] if p]
    if contact_parts:
        lines.append(' | '.join(contact_parts))
    lines.append('')

    if profile.get('summary'):
        lines.append('SUMMARY')
        lines.append(profile['summary'])
        lines.append('')

    # Build lookup: company+title → tailored bullets
    bullet_map: dict[str, list[str]] = {}
    for te in tailored.get('tailored_experience', []):
        key = f"{te.get('company', '')}|{te.get('title', '')}"
        bullet_map[key] = te.get('tailored_bullets', [])

    if profile.get('work_experience'):
        lines.append('EXPERIENCE')
        for exp in profile['work_experience']:
            date_str = f"{_format_date(exp.get('start_date'))} – {_format_date(exp.get('end_date'))}"
            lines.append(f"  {exp.get('company', '')}  {date_str}")
            lines.append(f"  {exp.get('title', '')}")
            key = f"{exp.get('company', '')}|{exp.get('title', '')}"
            bullets = bullet_map.get(key, exp.get('bullets', []))
            for b in bullets:
                lines.append(f"  • {b}")
            lines.append('')

    if profile.get('education'):
        lines.append('EDUCATION')
        for edu in profile['education']:
            date_str = _format_date(edu.get('graduation_date'))
            lines.append(f"  {edu.get('institution', '')}  {date_str}")
            lines.append(f"  {edu.get('degree', '')} in {edu.get('field_of_study', '')}")
            lines.append('')

    if profile.get('skills'):
        lines.append('SKILLS')
        lines.append('  ' + ', '.join(profile['skills']))
        lines.append('')

    return '\n'.join(lines)


# ---- Page-limit helpers -----------------------------------------------------

def _text_lines(text: str) -> float:
    """Estimate how many 10.5pt body lines a text string occupies (word-wrap)."""
    return max(1.0, math.ceil(len(text) / _CHARS_PER_LINE))


def _estimate_doc_lines(profile: dict, bullet_map: dict, options: dict) -> float:
    """
    Estimate the total line count of the rendered document.
    Uses fixed overheads per element type to account for font size and spacing.
    """
    lines = 0.0

    # Name (18pt ≈ 1.7× line height) + contact + trailing gap
    lines += 2.5   # name
    contact = profile.get('contact', {})
    contact_parts = [p for p in [
        contact.get('email'), contact.get('phone'),
        contact.get('location'), contact.get('linkedin')
    ] if p]
    if contact_parts:
        lines += 1.5   # contact line + gap

    # Summary
    if profile.get('summary'):
        lines += 2.5   # header
        lines += _text_lines(profile['summary']) + 0.5

    # Work experience
    work_exp = profile.get('work_experience', [])
    if work_exp:
        lines += 2.5   # section header
        for exp in work_exp:
            lines += 1.5   # employer row
            lines += 1.0   # title line
            key = f"{exp.get('company', '')}|{exp.get('title', '')}"
            bullets = bullet_map.get(key, exp.get('bullets', []))
            for b in bullets:
                lines += _text_lines(b) + 0.25
            lines += 0.5   # gap after entry

    # Education
    education = profile.get('education', [])
    if education:
        lines += 2.5   # section header
        for edu in education:
            lines += 1.5   # institution row
            lines += 1.0   # degree line
            for honor in edu.get('honors', []):
                lines += _text_lines(honor) + 0.25
            lines += 0.5

    # Skills
    if options.get('include_skills', True) and profile.get('skills'):
        lines += 2.5
        lines += _text_lines(', '.join(profile['skills'])) + 0.5

    # Projects
    if options.get('include_projects', False) and profile.get('projects'):
        lines += 2.5
        for proj in profile.get('projects', []):
            lines += 1.5
            if proj.get('description'):
                lines += _text_lines(proj['description']) + 0.25
            for b in proj.get('bullets', []):
                lines += _text_lines(b) + 0.25
            if proj.get('technologies'):
                lines += 1.0
            lines += 0.5

    # Certifications
    if options.get('include_certifications', True) and profile.get('certifications'):
        lines += 2.5
        for cert in profile['certifications']:
            lines += _text_lines(cert) + 0.25

    # Volunteer
    if options.get('include_volunteer', False) and profile.get('volunteer'):
        lines += 2.5
        for vol in profile['volunteer']:
            lines += _text_lines(vol) + 0.25

    # Languages
    if profile.get('languages'):
        lines += 2.5
        lines += _text_lines(', '.join(profile['languages'])) + 0.5

    return lines


def _trim_to_page_limit(
    profile: dict, tailored: dict, options: dict, max_pages: int
) -> tuple[dict, dict]:
    """
    Trim content so the resume fits within max_pages.

    Strategy (in order):
      1. Reduce bullets per job: 5 → 4 → 3 → 2 → 1
      2. Remove oldest work-experience entries (keep most recent)

    Works on deep copies; does not mutate the originals.
    """
    profile = copy.deepcopy(profile)
    tailored = copy.deepcopy(tailored)

    line_budget = max_pages * _LINES_PER_PAGE

    # Build a mutable bullet_map (company|title → list[str])
    bullet_map: dict[str, list[str]] = {}
    for te in tailored.get('tailored_experience', []):
        key = f"{te.get('company', '')}|{te.get('title', '')}"
        bullet_map[key] = te.get('tailored_bullets', [])

    def _sync_tailored() -> None:
        """Push bullet_map back into tailored['tailored_experience']."""
        for te in tailored.get('tailored_experience', []):
            key = f"{te.get('company', '')}|{te.get('title', '')}"
            if key in bullet_map:
                te['tailored_bullets'] = bullet_map[key]

    # Step 1: progressively reduce bullets per job
    for max_b in (5, 4, 3, 2, 1):
        if _estimate_doc_lines(profile, bullet_map, options) <= line_budget:
            break
        for exp in profile.get('work_experience', []):
            key = f"{exp.get('company', '')}|{exp.get('title', '')}"
            if key in bullet_map:
                bullet_map[key] = bullet_map[key][:max_b]
            else:
                exp['bullets'] = exp.get('bullets', [])[:max_b]

    _sync_tailored()

    # Step 2: drop oldest work-experience entries one at a time
    while (
        _estimate_doc_lines(profile, bullet_map, options) > line_budget
        and len(profile.get('work_experience', [])) > 1
    ):
        removed = profile['work_experience'].pop()
        removed_key = f"{removed.get('company', '')}|{removed.get('title', '')}"
        bullet_map.pop(removed_key, None)
        tailored['tailored_experience'] = [
            te for te in tailored.get('tailored_experience', [])
            if f"{te.get('company', '')}|{te.get('title', '')}" != removed_key
        ]

    return profile, tailored


# ---- Main builder -----------------------------------------------------------

def build(
    profile: dict,
    tailored: dict,
    options: dict
) -> tuple[io.BytesIO, str]:
    """
    Build a Harvard-style resume DOCX.

    Args:
        profile: MasterProfile dict.
        tailored: Result from GeminiProvider.tailor_bullets() —
                  { tailored_experience: [...], tailoring_notes: [...], ats_match_score: int }
        options: {
            include_skills: bool,
            include_projects: bool,
            include_certifications: bool,
            include_volunteer: bool,
            max_pages: int
        }

    Returns:
        (BytesIO DOCX bytes, preview_text string)
    """
    # Enforce page limit by trimming content before building the document
    max_pages = options.get('max_pages', 2)
    profile, tailored = _trim_to_page_limit(profile, tailored, options, max_pages)

    doc = Document()
    _set_margins(doc)

    # Remove default paragraph spacing from Normal style
    normal_style = doc.styles['Normal']
    normal_style.paragraph_format.space_before = Pt(0)
    normal_style.paragraph_format.space_after = Pt(0)

    contact = profile.get('contact', {})

    # --- Name ---
    name_para = doc.add_paragraph()
    name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name_para.paragraph_format.space_before = Pt(0)
    name_para.paragraph_format.space_after = Pt(4)
    name_run = name_para.add_run(contact.get('name', 'Full Name'))
    _set_font(name_run, 18, bold=True)

    # --- Contact line ---
    contact_parts = [p for p in [
        contact.get('email'), contact.get('phone'),
        contact.get('location'), contact.get('linkedin')
    ] if p]
    if contact_parts:
        contact_para = doc.add_paragraph()
        contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact_para.paragraph_format.space_before = Pt(0)
        contact_para.paragraph_format.space_after = Pt(6)
        contact_run = contact_para.add_run(' | '.join(contact_parts))
        _set_font(contact_run, 10.5)

    # --- Summary ---
    if profile.get('summary'):
        _add_section_header(doc, 'Summary')
        _add_body_para(doc, profile['summary'])

    # --- Experience ---
    work_exp = profile.get('work_experience', [])
    if work_exp:
        _add_section_header(doc, 'Experience')

        # Build lookup: company|title → tailored bullets
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
            bullets = bullet_map.get(key, exp.get('bullets', []))
            for b in bullets:
                _add_bullet(doc, b)

    # --- Education ---
    education = profile.get('education', [])
    if education:
        _add_section_header(doc, 'Education')
        for edu in education:
            date_str = _format_date(edu.get('graduation_date'))
            _add_employer_row(doc, edu.get('institution', ''), date_str)
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
            for b in proj.get('bullets', []):
                _add_bullet(doc, b)
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



    # --- Write to BytesIO ---
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)

    preview_text = _build_preview(profile, tailored)
    return buf, preview_text
