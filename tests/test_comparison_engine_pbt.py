"""Property-based tests for ComparisonEngine using Hypothesis."""
import sys
sys.path.insert(0, '/Users/navinkumar/workrepos/pers-prj/careerops')

import pytest
from hypothesis import given, strategies as st, settings, assume
from backend import ComparisonEngine, ComparisonError, CVParser


# --- Strategies for generating valid parsed CV dicts ---

def _text_content():
    """Generate non-empty text content."""
    return st.text(
        alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'), whitelist_characters='\n-|@*.#'),
        min_size=1,
        max_size=80,
    )


def _role_strategy(index):
    """Generate a single PE role dict."""
    return st.fixed_dictionaries({
        'key': st.just(f'role_{index}'),
        'title': st.builds(lambda t: f'### {t}', _text_content()),
        'metadata': st.builds(lambda m: f'**{m}**', _text_content()),
        'content': st.builds(lambda c: f'- {c}', _text_content()),
    })


@st.composite
def _roles_list(draw):
    """Generate a list of 1-3 PE roles."""
    count = draw(st.integers(min_value=1, max_value=3))
    roles = []
    for i in range(count):
        role = draw(_role_strategy(i))
        roles.append(role)
    return roles


@st.composite
def parsed_cv_strategy(draw):
    """Generate a valid parsed CV dict (output format of CVParser.parse())."""
    cv = {}

    # heading is always required
    cv['heading'] = draw(st.builds(lambda n: f'# {n}', _text_content()))

    # Optional categories (but we include them with high probability for testing)
    if draw(st.booleans()):
        cv['subheading'] = draw(st.builds(lambda t: f'**{t}**', _text_content()))

    if draw(st.booleans()):
        cv['contact'] = draw(st.builds(lambda e: f'{e}@test.com | City', _text_content()))

    if draw(st.booleans()):
        cv['summary'] = draw(st.builds(lambda s: f'## PROFESSIONAL SUMMARY\n\n{s}', _text_content()))

    if draw(st.booleans()):
        cv['core_skills'] = draw(st.builds(lambda s: f'## CORE SKILLS\n\n{s}', _text_content()))

    if draw(st.booleans()):
        roles = draw(_roles_list())
        cv['professional_experience'] = {
            'header': '## PROFESSIONAL EXPERIENCE',
            'roles': roles,
        }

    if draw(st.booleans()):
        cv['certifications'] = draw(st.builds(lambda c: f'## CERTIFICATIONS\n\n- {c}', _text_content()))

    if draw(st.booleans()):
        cv['education'] = draw(st.builds(lambda e: f'## EDUCATION\n\n- {e}', _text_content()))

    if draw(st.booleans()):
        cv['community'] = draw(st.builds(lambda c: f'## COMMUNITY LEADERSHIP & ENGAGEMENT\n\n- {c}', _text_content()))

    if draw(st.booleans()):
        cv['languages'] = draw(st.builds(lambda l: f'## LANGUAGES\n\n{l}', _text_content()))

    return cv


@st.composite
def parsed_cv_pair_with_whitespace_diff(draw):
    """Generate two parsed CVs that differ only by whitespace in some fields."""
    base = draw(parsed_cv_strategy())
    modified = dict(base)

    # Add whitespace to some string categories
    for key in list(modified.keys()):
        if key == 'professional_experience':
            continue
        if isinstance(modified[key], str) and draw(st.booleans()):
            padding = draw(st.text(alphabet=' \t\n', min_size=1, max_size=5))
            modified[key] = modified[key] + padding

    return base, modified


# --- Tests ---

engine = ComparisonEngine()


@settings(max_examples=100)
@given(original=parsed_cv_strategy(), suggested=parsed_cv_strategy())
def test_property4_changed_unchanged_classification(original, suggested):
    """Property 4: Changed/Unchanged Classification.

    'changed' is True iff content differs after trim.
    When unchanged, suggested_content equals original_content.
    """
    result = engine.compare(original, suggested)

    for key, entry in result.items():
        orig = entry['original_content']
        sugg = entry['suggested_content']
        changed = entry['changed']

        if orig.strip() == sugg.strip():
            # Should be marked as unchanged
            assert changed is False, (
                f"Key '{key}': content is identical after strip but marked changed.\n"
                f"  original_content: {repr(orig)}\n"
                f"  suggested_content: {repr(sugg)}"
            )
            # When unchanged, suggested_content must equal original_content
            assert sugg == orig, (
                f"Key '{key}': unchanged but suggested_content != original_content.\n"
                f"  original_content: {repr(orig)}\n"
                f"  suggested_content: {repr(sugg)}"
            )
        else:
            # Should be marked as changed
            assert changed is True, (
                f"Key '{key}': content differs after strip but not marked changed.\n"
                f"  original_content stripped: {repr(orig.strip())}\n"
                f"  suggested_content stripped: {repr(sugg.strip())}"
            )


@settings(max_examples=100)
@given(original=parsed_cv_strategy(), suggested=parsed_cv_strategy())
def test_property5_comparison_ordering_invariant(original, suggested):
    """Property 5: Comparison Ordering Invariant.

    Output keys follow CV_Category_Set order:
    top-level categories come in CATEGORY_ORDER, then PE roles appended after
    professional_experience.
    """
    result = engine.compare(original, suggested)
    result_keys = list(result.keys())

    # Build expected order: CATEGORY_ORDER categories that appear in result,
    # with PE role keys inserted right after 'professional_experience'
    expected_order = []
    for cat in CVParser.CATEGORY_ORDER:
        if cat in result_keys:
            expected_order.append(cat)
            if cat == 'professional_experience':
                # Collect PE role keys in order
                role_keys = [k for k in result_keys if k.startswith('professional_experience.role_')]
                role_keys.sort(key=lambda k: int(k.split('_')[-1]))
                expected_order.extend(role_keys)

    assert result_keys == expected_order, (
        f"Key ordering mismatch.\n"
        f"  Expected: {expected_order}\n"
        f"  Actual:   {result_keys}"
    )


@settings(max_examples=100)
@given(original=parsed_cv_strategy(), suggested=parsed_cv_strategy())
def test_property6_comparison_completeness(original, suggested):
    """Property 6: Comparison Completeness.

    Output contains entry for every category present in either input + all PE roles.
    """
    result = engine.compare(original, suggested)

    # Check all non-PE categories present in either input have an entry
    for cat in CVParser.CATEGORY_ORDER:
        if cat == 'professional_experience':
            # PE header key should exist if either input has PE
            orig_pe = original.get('professional_experience')
            sugg_pe = suggested.get('professional_experience')
            if orig_pe or sugg_pe:
                assert 'professional_experience' in result, (
                    "professional_experience key missing from result but present in input"
                )
                # All roles from either side should be represented
                orig_roles = orig_pe.get('roles', []) if isinstance(orig_pe, dict) else []
                sugg_roles = sugg_pe.get('roles', []) if isinstance(sugg_pe, dict) else []
                max_roles = max(len(orig_roles), len(sugg_roles))
                for i in range(max_roles):
                    role_key = f'professional_experience.role_{i}'
                    assert role_key in result, (
                        f"Expected role key '{role_key}' in result. "
                        f"orig_roles={len(orig_roles)}, sugg_roles={len(sugg_roles)}"
                    )
            else:
                # Even if neither has PE, the compare loop still creates an entry
                # with empty content (since it iterates CATEGORY_ORDER)
                assert 'professional_experience' in result
        else:
            # The engine iterates over all CATEGORY_ORDER, so every category
            # should appear in result regardless of input presence
            assert cat in result, (
                f"Category '{cat}' missing from comparison result"
            )

    # Verify every entry has required fields
    for key, entry in result.items():
        assert 'original_content' in entry, f"Key '{key}' missing 'original_content'"
        assert 'suggested_content' in entry, f"Key '{key}' missing 'suggested_content'"
        assert 'changed' in entry, f"Key '{key}' missing 'changed'"
        assert 'score_impact' in entry, f"Key '{key}' missing 'score_impact'"
        assert isinstance(entry['changed'], bool), f"Key '{key}' 'changed' is not bool"
        assert isinstance(entry['score_impact'], int), f"Key '{key}' 'score_impact' is not int"
