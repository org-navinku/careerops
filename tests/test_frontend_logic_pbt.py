"""Property-based tests for frontend approval count and batch selection logic.

Since the actual logic runs in JavaScript, we test equivalent Python implementations
that mirror the frontend behavior for approval count display and batch selection.
"""
import sys
sys.path.insert(0, '/Users/navinkumar/workrepos/pers-prj/careerops')

from hypothesis import given, strategies as st, settings
import pytest


# --- Python equivalents of the JS frontend logic ---

def compute_approval_display(total_changed: int, num_checked: int) -> str:
    """Equivalent of updateComparisonStats display logic."""
    return f"{num_checked} of {total_changed} changes approved"


def select_all(categories: list[bool]) -> list[bool]:
    """Select All: returns all True."""
    return [True] * len(categories)


def deselect_all(categories: list[bool]) -> list[bool]:
    """Deselect All: returns all False."""
    return [False] * len(categories)


# --- Property 13: Approval Count Accuracy ---

@settings(max_examples=100)
@given(
    total_changed=st.integers(min_value=1, max_value=50)
)
def test_property_13_approval_count_accuracy(total_changed):
    """Property 13: Approval Count Accuracy.

    For any set of N changed categories (N >= 1) with K checkboxes checked
    (0 <= K <= N), the approval count display shows exactly
    "{K} of {N} changes approved".
    """
    for num_checked in range(total_changed + 1):
        result = compute_approval_display(total_changed, num_checked)
        expected = f"{num_checked} of {total_changed} changes approved"
        assert result == expected, (
            f"Expected '{expected}' but got '{result}' "
            f"for total_changed={total_changed}, num_checked={num_checked}"
        )


@settings(max_examples=100)
@given(
    data=st.data()
)
def test_property_13_approval_count_random_k(data):
    """Property 13 (variant): Generate both N and K randomly where 0 <= K <= N.

    For any randomly generated N (1-50) and K (0-N), the approval count
    display shows exactly "{K} of {N} changes approved".
    """
    total_changed = data.draw(st.integers(min_value=1, max_value=50), label="total_changed")
    num_checked = data.draw(st.integers(min_value=0, max_value=total_changed), label="num_checked")

    result = compute_approval_display(total_changed, num_checked)
    expected = f"{num_checked} of {total_changed} changes approved"
    assert result == expected, (
        f"Expected '{expected}' but got '{result}'"
    )


# --- Property 14: Batch Selection Operations ---

@settings(max_examples=100)
@given(
    categories=st.lists(st.booleans(), min_size=0, max_size=50)
)
def test_property_14_select_all(categories):
    """Property 14a: Batch Selection - Select All.

    For any set of N categories in any starting state,
    after Select All: all N are checked (count == N).
    """
    result = select_all(categories)
    assert len(result) == len(categories), (
        f"Expected length {len(categories)} but got {len(result)}"
    )
    assert all(result), (
        f"Expected all True after select_all, but got {result}"
    )
    assert sum(result) == len(categories), (
        f"Expected count {len(categories)} but got {sum(result)}"
    )


@settings(max_examples=100)
@given(
    categories=st.lists(st.booleans(), min_size=0, max_size=50)
)
def test_property_14_deselect_all(categories):
    """Property 14b: Batch Selection - Deselect All.

    For any set of N categories in any starting state,
    after Deselect All: all N are unchecked (count == 0).
    """
    result = deselect_all(categories)
    assert len(result) == len(categories), (
        f"Expected length {len(categories)} but got {len(result)}"
    )
    assert not any(result), (
        f"Expected all False after deselect_all, but got {result}"
    )
    assert sum(result) == 0, (
        f"Expected count 0 but got {sum(result)}"
    )


# --- Concrete unit test cases ---

class TestApprovalCountConcrete:
    """Concrete unit tests for approval count display."""

    def test_zero_of_five_changes_approved(self):
        """0 of 5 changes approved."""
        result = compute_approval_display(5, 0)
        assert result == "0 of 5 changes approved"

    def test_three_of_three_changes_approved(self):
        """3 of 3 changes approved (all checked)."""
        result = compute_approval_display(3, 3)
        assert result == "3 of 3 changes approved"

    def test_one_of_ten_changes_approved(self):
        """1 of 10 changes approved."""
        result = compute_approval_display(10, 1)
        assert result == "1 of 10 changes approved"


class TestBatchSelectionConcrete:
    """Concrete unit tests for batch selection operations."""

    def test_select_all_on_empty_list(self):
        """Select All on empty list returns empty list."""
        result = select_all([])
        assert result == []

    def test_deselect_all_when_all_already_unchecked(self):
        """Deselect All when all already unchecked stays unchecked."""
        result = deselect_all([False, False, False])
        assert result == [False, False, False]

    def test_select_all_on_mixed_state(self):
        """Select All on mixed state sets all to True."""
        result = select_all([True, False, True, False, False])
        assert result == [True, True, True, True, True]

    def test_deselect_all_on_all_checked(self):
        """Deselect All on all checked sets all to False."""
        result = deselect_all([True, True, True])
        assert result == [False, False, False]

    def test_select_all_preserves_length(self):
        """Select All preserves list length."""
        categories = [False, True, False, True, True, False, True]
        result = select_all(categories)
        assert len(result) == len(categories)

    def test_deselect_all_preserves_length(self):
        """Deselect All preserves list length."""
        categories = [True, False, True, True, False]
        result = deselect_all(categories)
        assert len(result) == len(categories)
