"""Property-based tests for CVParser using Hypothesis."""
import sys
sys.path.insert(0, '/Users/navinkumar/workrepos/pers-prj/careerops')

import re
from hypothesis import given, strategies as st, settings, HealthCheck, assume
import backend
from backend import CVParser, ParseError


# --- Hypothesis Strategies ---

def _safe_text():
    """Generate text that won't be confused for markdown headers or special lines."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=('L', 'N', 'P', 'Z'),
            blacklist_characters='#*@|\n\r'
        ),
        min_size=3,
        max_size=40,
    ).map(lambda s: s.strip()).filter(lambda s: len(s) >= 3)


def _bullet_line():
    """Generate a bullet-point line."""
    return _safe_text().map(lambda t: f"- {t}")


def _section_content(min_lines=1, max_lines=4):
    """Generate content lines for a section (bullet points or plain text)."""
    return st.lists(_bullet_line(), min_size=min_lines, max_size=max_lines).map(
        lambda lines: '\n'.join(lines)
    )


@st.composite
def cv_markdown(draw, min_roles=1, max_roles=4):
    """Generate a valid CV markdown document with all 10 category headers."""
    parts = []

    # 1. Heading (H1)
    name = draw(_safe_text())
    parts.append(f"# {name}")
    parts.append('')

    # 2. Subheading (bold line)
    subtitle = draw(_safe_text())
    parts.append(f"**{subtitle}**")
    parts.append('')

    # 3. Contact line (must contain @ and |)
    email_user = draw(st.from_regex(r'[a-z]{3,8}', fullmatch=True))
    email_domain = draw(st.from_regex(r'[a-z]{3,6}', fullmatch=True))
    phone = draw(st.from_regex(r'[0-9]{10}', fullmatch=True))
    location = draw(_safe_text())
    contact = f"{email_user}@{email_domain}.com | {phone} | {location}"
    parts.append(contact)
    parts.append('')

    # 4. Professional Summary
    parts.append('## Professional Summary')
    summary_content = draw(_section_content())
    parts.append(summary_content)
    parts.append('')

    # 5. Core Skills
    parts.append('## Core Skills')
    skills_content = draw(_section_content())
    parts.append(skills_content)
    parts.append('')

    # 6. Professional Experience with N roles
    num_roles = draw(st.integers(min_value=min_roles, max_value=max_roles))
    parts.append('## Professional Experience')
    parts.append('')

    for r in range(num_roles):
        role_title = draw(_safe_text())
        company = draw(_safe_text())
        parts.append(f"### {role_title} at {company}")
        # Metadata line (bold)
        dates = draw(st.from_regex(r'[A-Z][a-z]{2} 20[12][0-9]', fullmatch=True))
        parts.append(f"**{dates} - Present**")
        parts.append('')
        role_content = draw(_section_content(min_lines=1, max_lines=3))
        parts.append(role_content)
        parts.append('')

    # 7. Certifications
    parts.append('## Certifications')
    certs_content = draw(_section_content())
    parts.append(certs_content)
    parts.append('')

    # 8. Education
    parts.append('## Education')
    edu_content = draw(_section_content())
    parts.append(edu_content)
    parts.append('')

    # 9. Community Leadership & Engagement
    parts.append('## Community Leadership & Engagement')
    community_content = draw(_section_content())
    parts.append(community_content)
    parts.append('')

    # 10. Languages
    parts.append('## Languages')
    lang_content = draw(_section_content())
    parts.append(lang_content)
    parts.append('')

    return '\n'.join(parts)


@st.composite
def cv_markdown_with_role_count(draw):
    """Generate a CV markdown along with expected role count."""
    num_roles = draw(st.integers(min_value=1, max_value=4))
    md = draw(cv_markdown(min_roles=num_roles, max_roles=num_roles))
    return md, num_roles


def _normalize_whitespace(text: str) -> str:
    """Normalize whitespace for comparison: collapse runs of whitespace to single space."""
    return re.sub(r'\s+', ' ', text).strip()


# --- Property-Based Tests ---

parser = CVParser()


@given(md=cv_markdown())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_parse_serialize_round_trip(md):
    """Property 1: parse then serialize produces equivalent content (whitespace-normalized)."""
    categories = parser.parse(md)
    serialized = parser.serialize(categories)

    # Re-parse the serialized output
    re_parsed = parser.parse(serialized)
    re_serialized = parser.serialize(re_parsed)

    # Normalized comparison: the serialize output should be stable after one round-trip
    assert _normalize_whitespace(serialized) == _normalize_whitespace(re_serialized)


@given(data=cv_markdown_with_role_count())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_category_parsing_completeness(data):
    """Property 2: CV with all 10 headers and N roles produces exactly 10 top-level entries and N roles."""
    md, expected_roles = data
    categories = parser.parse(md)

    # All 10 category keys should be present
    for key in CVParser.CATEGORY_ORDER:
        assert key in categories, f"Missing category key: {key}"

    # Exactly 10 top-level entries
    assert len([k for k in CVParser.CATEGORY_ORDER if k in categories]) == 10

    # Professional Experience should have exactly N roles
    pe = categories['professional_experience']
    assert isinstance(pe, dict)
    assert 'roles' in pe
    assert len(pe['roles']) == expected_roles


@given(md=cv_markdown())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_unmapped_content_assignment(md):
    """Property 3: lines between headers append to nearest preceding category.

    We verify this by adding unmapped lines after a known section and confirming
    they end up in that section's content.
    """
    # Insert unmapped lines after the ## Core Skills section content
    marker = "UNMAPPED_MARKER_LINE_XYZ"
    # Find the Core Skills section and insert extra content after it
    lines = md.split('\n')
    new_lines = []
    inserted = False
    in_core_skills = False

    for i, line in enumerate(lines):
        new_lines.append(line)
        if line.strip() == '## Core Skills':
            in_core_skills = True
        elif in_core_skills and not inserted and line.strip().startswith('## '):
            # Insert unmapped content just before the next H2
            # Actually insert BEFORE this line
            new_lines.pop()  # remove the H2 we just added
            new_lines.append(f"- {marker}")
            new_lines.append('')
            new_lines.append(line)  # re-add the H2
            inserted = True
            in_core_skills = False

    if not inserted and in_core_skills:
        # Core Skills was last section, append at end
        new_lines.append(f"- {marker}")
        inserted = True

    assume(inserted)
    modified_md = '\n'.join(new_lines)

    categories = parser.parse(modified_md)

    # The marker should appear in the core_skills category
    core_skills_content = categories.get('core_skills', '')
    assert marker in core_skills_content, (
        f"Unmapped content '{marker}' not found in core_skills. "
        f"core_skills content: {core_skills_content[:200]}"
    )
