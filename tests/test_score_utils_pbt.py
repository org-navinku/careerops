"""Property-based tests for compute_ats_score and truncate_text using Hypothesis."""
import sys
sys.path.insert(0, '/Users/navinkumar/workrepos/pers-prj/careerops')

from hypothesis import given, strategies as st, settings, assume
import backend
from backend import compute_ats_score, truncate_text


# ========== Helper ==========

def clamp(value, lo, hi):
    """Reference clamp implementation for test assertions."""
    return max(lo, min(hi, value))


# ========== Property 7: Text Truncation ==========


@settings(max_examples=100)
@given(
    text=st.text(min_size=0, max_size=500),
    max_len=st.integers(min_value=0, max_value=600),
)
def test_truncate_text_property(text, max_len):
    """Property 7: truncate_text returns unchanged text if short, else text[:M] + '…'."""
    result = truncate_text(text, max_len)

    if len(text) <= max_len:
        # Text fits: must be returned unchanged
        assert result == text
    else:
        # Text exceeds max_len: truncated with ellipsis
        assert result == text[:max_len] + '…'
        assert len(result) == max_len + 1  # +1 for the ellipsis character


def test_truncate_text_max_len_zero_empty_string():
    """Edge case: empty string with max_len=0 returns unchanged."""
    result = truncate_text('', 0)
    assert result == ''


def test_truncate_text_max_len_zero_nonempty_string():
    """Edge case: non-empty string with max_len=0 truncates to just ellipsis."""
    result = truncate_text('hello', 0)
    assert result == '…'
    assert len(result) == 1


def test_truncate_text_exact_boundary():
    """Edge case: text length equals max_len — no truncation."""
    text = 'abcde'
    result = truncate_text(text, 5)
    assert result == text


def test_truncate_text_one_over_boundary():
    """Edge case: text is one character longer than max_len."""
    text = 'abcdef'
    result = truncate_text(text, 5)
    assert result == 'abcde…'


# ========== Property 8: ATS Score Computation ==========


@settings(max_examples=100)
@given(
    baseline=st.integers(min_value=0, max_value=100),
    impacts=st.dictionaries(
        keys=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N', 'P'))),
        values=st.integers(min_value=-50, max_value=50),
        max_size=10,
    ),
    data=st.data(),
)
def test_ats_score_computation_property(baseline, impacts, data):
    """Property 8: compute_ats_score correctly clamps sum of approved impacts."""
    # Generate a random subset of impacts keys as approved
    if impacts:
        approved_keys = data.draw(
            st.lists(st.sampled_from(list(impacts.keys())), unique=True)
        )
    else:
        approved_keys = []

    approvals = {key: True for key in approved_keys}

    result = compute_ats_score(baseline, impacts, approvals)

    # Verify current_score
    approved_sum = sum(impacts[k] for k in approved_keys)
    expected_current = clamp(baseline + approved_sum, 0, 100)
    assert result['current_score'] == expected_current

    # Verify max_score
    total_sum = sum(impacts.values())
    expected_max = clamp(baseline + total_sum, 0, 100)
    assert result['max_score'] == expected_max

    # Both scores must be in [0, 100]
    assert 0 <= result['current_score'] <= 100
    assert 0 <= result['max_score'] <= 100


@settings(max_examples=100)
@given(
    baseline=st.integers(min_value=0, max_value=100),
    impacts=st.dictionaries(
        keys=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N', 'P'))),
        values=st.integers(min_value=0, max_value=50),
        max_size=10,
    ),
    data=st.data(),
)
def test_ats_score_current_leq_max_when_nonnegative(baseline, impacts, data):
    """When all impacts are non-negative, current_score <= max_score."""
    if impacts:
        approved_keys = data.draw(
            st.lists(st.sampled_from(list(impacts.keys())), unique=True)
        )
    else:
        approved_keys = []

    approvals = {key: True for key in approved_keys}

    result = compute_ats_score(baseline, impacts, approvals)
    assert result['current_score'] <= result['max_score']


def test_ats_score_empty_impacts():
    """Edge case: empty impacts dict — both scores equal baseline."""
    result = compute_ats_score(75, {}, {})
    assert result['current_score'] == 75
    assert result['max_score'] == 75


def test_ats_score_empty_approvals():
    """Edge case: empty approvals dict — current_score equals baseline, max accounts for all impacts."""
    impacts = {'a': 10, 'b': 5, 'c': -3}
    result = compute_ats_score(60, impacts, {})
    assert result['current_score'] == 60
    assert result['max_score'] == clamp(60 + 10 + 5 - 3, 0, 100)


def test_ats_score_all_negative_impacts():
    """Edge case: all negative impacts."""
    impacts = {'a': -20, 'b': -30, 'c': -15}
    approvals = {'a': True, 'b': True, 'c': True}
    result = compute_ats_score(50, impacts, approvals)
    assert result['current_score'] == clamp(50 - 20 - 30 - 15, 0, 100)
    assert result['max_score'] == clamp(50 - 20 - 30 - 15, 0, 100)


def test_ats_score_baseline_zero():
    """Edge case: baseline at lower boundary (0)."""
    impacts = {'x': 10, 'y': -5}
    approvals = {'x': True, 'y': True}
    result = compute_ats_score(0, impacts, approvals)
    assert result['current_score'] == clamp(0 + 10 - 5, 0, 100)
    assert result['max_score'] == clamp(0 + 10 - 5, 0, 100)


def test_ats_score_baseline_hundred():
    """Edge case: baseline at upper boundary (100)."""
    impacts = {'x': 10, 'y': 5}
    approvals = {'x': True, 'y': True}
    result = compute_ats_score(100, impacts, approvals)
    # Clamped to 100
    assert result['current_score'] == 100
    assert result['max_score'] == 100


def test_ats_score_clamps_below_zero():
    """Edge case: large negative impacts should clamp to 0."""
    impacts = {'a': -80, 'b': -50}
    approvals = {'a': True, 'b': True}
    result = compute_ats_score(10, impacts, approvals)
    assert result['current_score'] == 0
    assert result['max_score'] == 0


def test_ats_score_partial_approval():
    """Only approved impacts contribute to current_score."""
    impacts = {'a': 10, 'b': 20, 'c': 5}
    approvals = {'a': True, 'c': True}  # b not approved
    result = compute_ats_score(50, impacts, approvals)
    assert result['current_score'] == clamp(50 + 10 + 5, 0, 100)
    assert result['max_score'] == clamp(50 + 10 + 20 + 5, 0, 100)
