"""Property-based tests for FinalAssembler using Hypothesis."""
import sys
from hypothesis import given, strategies as st, settings, HealthCheck, assume

sys.path.insert(0, '/Users/navinkumar/workrepos/pers-prj/careerops')

import pytest
from backend import FinalAssembler, AssemblyError, CVParser


# --- Strategies ---

CATEGORY_ORDER = CVParser.CATEGORY_ORDER

# Markdown content fragments for generating realistic content
md_headings = st.sampled_from(['# ', '## ', '### '])
md_bullets = st.sampled_from(['- ', '- **bold** ', '- [link](http://example.com) '])


@st.composite
def unique_markdown_content(draw, label):
    """Generate markdown content with a unique label embedded to avoid collisions."""
    lines = []
    # Optionally start with a heading
    if draw(st.booleans()):
        heading = draw(md_headings)
        title = draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz', min_size=3, max_size=15))
        lines.append(f'{heading}{title.strip()} {label}')
    else:
        lines.append(f'Content for {label}')
    # Add 1-3 content lines
    num_lines = draw(st.integers(min_value=1, max_value=3))
    for i in range(num_lines):
        choice = draw(st.integers(min_value=0, max_value=2))
        if choice == 0:
            text = draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ,.', min_size=3, max_size=20))
            lines.append(f'{text.strip()} {label}_line{i}')
        elif choice == 1:
            bullet = draw(md_bullets)
            text = draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ', min_size=3, max_size=15))
            lines.append(f'{bullet}{text.strip()} {label}_line{i}')
        else:
            text = draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ', min_size=3, max_size=10))
            lines.append(f'**{text.strip()} {label}_line{i}**')
    return '\n'.join(lines)


@st.composite
def comparison_entry(draw, cat_key):
    """Generate a valid comparison entry for a given category key."""
    original = draw(unique_markdown_content(f'{cat_key}_orig'))
    changed = draw(st.booleans())
    if changed:
        suggested = draw(unique_markdown_content(f'{cat_key}_sugg'))
    else:
        suggested = original
    score_impact = draw(st.integers(min_value=0, max_value=10)) if changed else 0
    return {
        'original_content': original,
        'suggested_content': suggested,
        'changed': changed,
        'score_impact': score_impact,
    }


@st.composite
def comparison_and_approvals(draw):
    """Generate a valid comparison dict and approvals dict with at least one True."""
    comparison = {}
    approvals = {}

    # Choose which non-PE categories to include (at least one)
    non_pe_cats = [c for c in CATEGORY_ORDER if c != 'professional_experience']
    included_cats = draw(st.lists(
        st.sampled_from(non_pe_cats),
        min_size=1,
        max_size=len(non_pe_cats),
        unique=True,
    ))

    # Always include professional_experience to test PE roles
    include_pe = draw(st.booleans())

    for cat in included_cats:
        entry = draw(comparison_entry(cat))
        comparison[cat] = entry
        approvals[cat] = draw(st.booleans())

    if include_pe:
        # PE header
        pe_header = draw(comparison_entry('professional_experience'))
        comparison['professional_experience'] = pe_header
        approvals['professional_experience'] = draw(st.booleans())

        # PE roles (1-3)
        num_roles = draw(st.integers(min_value=1, max_value=3))
        for i in range(num_roles):
            role_key = f'professional_experience.role_{i}'
            role_entry = draw(comparison_entry(role_key))
            comparison[role_key] = role_entry
            approvals[role_key] = draw(st.booleans())

    # Ensure at least one approval is True
    if not any(approvals.values()):
        # Force one to True
        key = draw(st.sampled_from(list(approvals.keys())))
        approvals[key] = True

    return comparison, approvals


# --- Property Tests ---

@given(data=comparison_and_approvals())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property_9_assembly_content_selection(data):
    """Property 9: For each category, if approved the assembled CV contains
    suggested_content, if not it contains original_content."""
    comparison, approvals = data
    assembler = FinalAssembler()
    result = assembler.assemble(comparison, approvals)

    for key, entry in comparison.items():
        approved = approvals.get(key, False)
        expected_content = entry['suggested_content'] if approved else entry['original_content']
        if expected_content:
            # Each line of expected content should appear in result
            for line in expected_content.strip().splitlines():
                line_stripped = line.strip()
                if line_stripped:
                    assert line_stripped in result, (
                        f"Expected content line '{line_stripped}' from key '{key}' "
                        f"(approved={approved}) not found in result"
                    )


@given(data=comparison_and_approvals())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property_10_assembly_ordering(data):
    """Property 10: Categories appear in CATEGORY_ORDER in the output."""
    comparison, approvals = data
    assembler = FinalAssembler()
    result = assembler.assemble(comparison, approvals)

    # Collect positions of each category's content in result using unique markers
    # We use 'Content for <cat>_' or the full first line as a unique anchor
    positions = {}
    for cat_key in CATEGORY_ORDER:
        if cat_key == 'professional_experience':
            entry = comparison.get('professional_experience')
            if entry:
                approved = approvals.get('professional_experience', False)
                content = entry['suggested_content'] if approved else entry['original_content']
                if content and content.strip():
                    first_line = content.strip().splitlines()[0]
                    pos = result.find(first_line)
                    if pos >= 0:
                        positions[cat_key] = pos
        else:
            entry = comparison.get(cat_key)
            if entry:
                approved = approvals.get(cat_key, False)
                content = entry['suggested_content'] if approved else entry['original_content']
                if content and content.strip():
                    first_line = content.strip().splitlines()[0]
                    pos = result.find(first_line)
                    if pos >= 0:
                        positions[cat_key] = pos

    # Verify ordering
    ordered_cats = [c for c in CATEGORY_ORDER if c in positions]
    for i in range(len(ordered_cats) - 1):
        cat_a = ordered_cats[i]
        cat_b = ordered_cats[i + 1]
        assert positions[cat_a] < positions[cat_b], (
            f"Category '{cat_a}' (pos={positions[cat_a]}) should appear before "
            f"'{cat_b}' (pos={positions[cat_b]}) in the output"
        )


@given(data=comparison_and_approvals())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property_11_assembly_category_uniqueness(data):
    """Property 11: Each category's content appears exactly once."""
    comparison, approvals = data
    assembler = FinalAssembler()
    result = assembler.assemble(comparison, approvals)

    for key, entry in comparison.items():
        approved = approvals.get(key, False)
        content = entry['suggested_content'] if approved else entry['original_content']
        if content and content.strip():
            # Use the unique label embedded in content to verify uniqueness
            suffix = 'sugg' if approved else 'orig'
            label = f'{key}_{suffix}'
            count = result.count(label)
            # The label appears in the first line and potentially in content lines
            # Check that the full content block appears exactly once
            content_stripped = content.strip()
            block_count = result.count(content_stripped)
            assert block_count == 1, (
                f"Content for key '{key}' appears {block_count} times, expected 1. "
                f"Content starts with: '{content_stripped[:60]}...'"
            )


@given(data=comparison_and_approvals())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property_12_formatting_preservation(data):
    """Property 12: Markdown tokens (# ## ### - ** [](url)) in content are preserved."""
    comparison, approvals = data
    assembler = FinalAssembler()
    result = assembler.assemble(comparison, approvals)

    import re

    # Markdown token patterns to check
    md_token_patterns = [
        r'^#{1,3}\s',     # headings: # ## ###
        r'^- ',           # bullet points
        r'\*\*[^*]+\*\*', # bold text
        r'\[.*?\]\(.*?\)',# links [text](url)
    ]

    for key, entry in comparison.items():
        approved = approvals.get(key, False)
        content = entry['suggested_content'] if approved else entry['original_content']
        if not content:
            continue

        for line in content.splitlines():
            for pattern in md_token_patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    assert match in result, (
                        f"Markdown token '{match}' from key '{key}' not preserved in output"
                    )
