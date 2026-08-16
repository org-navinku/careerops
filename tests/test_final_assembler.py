"""Unit tests for FinalAssembler class."""
import sys

sys.path.insert(0, '/Users/navinkumar/workrepos/pers-prj/careerops')

import pytest
import backend
from backend import FinalAssembler, AssemblyError, CVParser


# --- Test fixtures ---

def make_comparison():
    """Create a standard comparison dict for testing."""
    return {
        'heading': {
            'original_content': '# John Doe',
            'suggested_content': '# John Doe',
            'changed': False,
            'score_impact': 0,
        },
        'contact': {
            'original_content': 'john@example.com | 555-1234',
            'suggested_content': 'john@example.com | 555-1234',
            'changed': False,
            'score_impact': 0,
        },
        'summary': {
            'original_content': '## PROFESSIONAL SUMMARY\n\nExperienced engineer with 10 years.',
            'suggested_content': '## PROFESSIONAL SUMMARY\n\nSenior engineer specializing in cloud.',
            'changed': True,
            'score_impact': 5,
        },
        'core_skills': {
            'original_content': '## CORE SKILLS\n\n- Python\n- AWS\n- Docker',
            'suggested_content': '## CORE SKILLS\n\n- Python\n- AWS\n- Kubernetes\n- Terraform',
            'changed': True,
            'score_impact': 3,
        },
        'professional_experience': {
            'original_content': '## PROFESSIONAL EXPERIENCE',
            'suggested_content': '## PROFESSIONAL EXPERIENCE',
            'changed': False,
            'score_impact': 0,
        },
        'professional_experience.role_0': {
            'original_content': '### Senior Engineer — Acme Corp\n**Jan 2020 – Present**\n- Led team of 5\n- Built microservices',
            'suggested_content': '### Senior Engineer — Acme Corp\n**Jan 2020 – Present**\n- Led team of 5 engineers\n- Architected cloud-native microservices',
            'changed': True,
            'score_impact': 4,
        },
        'professional_experience.role_1': {
            'original_content': '### Engineer — Beta Inc\n**Jun 2017 – Dec 2019**\n- Developed APIs\n- Maintained CI/CD',
            'suggested_content': '### Engineer — Beta Inc\n**Jun 2017 – Dec 2019**\n- Designed RESTful APIs\n- Implemented CI/CD pipelines with Jenkins',
            'changed': True,
            'score_impact': 2,
        },
        'education': {
            'original_content': '## EDUCATION\n\n### BSc Computer Science\n**University of Example, 2017**',
            'suggested_content': '## EDUCATION\n\n### BSc Computer Science\n**University of Example, 2017**',
            'changed': False,
            'score_impact': 0,
        },
    }


def make_all_approvals(comparison):
    """Create approvals dict with all True for given comparison."""
    return {key: True for key in comparison.keys()}


def make_no_approvals(comparison):
    """Create approvals dict with all False for given comparison."""
    return {key: False for key in comparison.keys()}


# --- Tests ---

class TestFinalAssemblerZeroApprovals:
    """Test that zero approvals raises AssemblyError."""

    def test_all_false_raises_assembly_error(self):
        """All approvals set to False should raise AssemblyError."""
        comparison = make_comparison()
        approvals = make_no_approvals(comparison)
        assembler = FinalAssembler()

        with pytest.raises(backend.AssemblyError):
            assembler.assemble(comparison, approvals)

    def test_empty_approvals_dict_raises_assembly_error(self):
        """Empty approvals dict should raise AssemblyError."""
        comparison = make_comparison()
        approvals = {}
        assembler = FinalAssembler()

        with pytest.raises(backend.AssemblyError):
            assembler.assemble(comparison, approvals)


class TestFinalAssemblerAllApprovals:
    """Test that all approvals produces CV with all suggested_content."""

    def test_all_approved_uses_suggested_content(self):
        """When all categories are approved, result contains all suggested_content."""
        comparison = make_comparison()
        approvals = make_all_approvals(comparison)
        assembler = FinalAssembler()

        result = assembler.assemble(comparison, approvals)

        for key, entry in comparison.items():
            suggested = entry['suggested_content']
            if suggested:
                for line in suggested.strip().splitlines():
                    if line.strip():
                        assert line.strip() in result, (
                            f"Suggested content line '{line.strip()}' for key '{key}' not in result"
                        )

    def test_all_approved_does_not_contain_differing_original(self):
        """When all categories are approved, changed entries should not use original."""
        comparison = make_comparison()
        approvals = make_all_approvals(comparison)
        assembler = FinalAssembler()

        result = assembler.assemble(comparison, approvals)

        # Check specific unique-to-original content that cannot be a substring of suggested
        # summary original has 'Experienced engineer with 10 years' which is not in suggested
        assert 'Experienced engineer with 10 years.' not in result
        # core_skills original has 'Docker' which is not in suggested
        assert '- Docker' not in result
        # role_1 original has 'Maintained CI/CD' which is not in suggested
        assert 'Maintained CI/CD' not in result


class TestFinalAssemblerSingleApproval:
    """Test single approval uses suggested for that category, original for rest."""

    def test_single_approval_summary(self):
        """Approving only summary uses suggested for summary, original for others."""
        comparison = make_comparison()
        approvals = {key: False for key in comparison.keys()}
        approvals['summary'] = True

        assembler = FinalAssembler()
        result = assembler.assemble(comparison, approvals)

        # Summary should use suggested
        assert 'Senior engineer specializing in cloud.' in result
        assert 'Experienced engineer with 10 years.' not in result

        # core_skills should use original
        assert '- Python\n- AWS\n- Docker' in result

        # PE role_0 should use original
        assert '- Built microservices' in result

    def test_single_approval_core_skills(self):
        """Approving only core_skills uses suggested for it, original for rest."""
        comparison = make_comparison()
        approvals = {key: False for key in comparison.keys()}
        approvals['core_skills'] = True

        assembler = FinalAssembler()
        result = assembler.assemble(comparison, approvals)

        # core_skills should use suggested
        assert '- Kubernetes' in result
        assert '- Terraform' in result

        # summary should use original
        assert 'Experienced engineer with 10 years.' in result


class TestFinalAssemblerPERoleApprovals:
    """Test PE role-level approvals."""

    def test_approve_role_0_not_role_1(self):
        """Approving role_0 but not role_1 gives suggested for role_0, original for role_1."""
        comparison = make_comparison()
        approvals = {key: False for key in comparison.keys()}
        approvals['professional_experience.role_0'] = True

        assembler = FinalAssembler()
        result = assembler.assemble(comparison, approvals)

        # role_0 should use suggested
        assert 'Architected cloud-native microservices' in result
        assert 'Built microservices' not in result

        # role_1 should use original
        assert 'Developed APIs' in result
        assert 'Maintained CI/CD' in result
        assert 'Designed RESTful APIs' not in result

    def test_approve_role_1_not_role_0(self):
        """Approving role_1 but not role_0 gives suggested for role_1, original for role_0."""
        comparison = make_comparison()
        approvals = {key: False for key in comparison.keys()}
        approvals['professional_experience.role_1'] = True

        assembler = FinalAssembler()
        result = assembler.assemble(comparison, approvals)

        # role_1 should use suggested
        assert 'Designed RESTful APIs' in result
        assert 'Implemented CI/CD pipelines with Jenkins' in result
        assert 'Developed APIs' not in result

        # role_0 should use original
        assert 'Built microservices' in result
        assert 'Architected cloud-native microservices' not in result

    def test_approve_both_roles(self):
        """Approving both roles uses suggested for both."""
        comparison = make_comparison()
        approvals = {key: False for key in comparison.keys()}
        approvals['professional_experience.role_0'] = True
        approvals['professional_experience.role_1'] = True

        assembler = FinalAssembler()
        result = assembler.assemble(comparison, approvals)

        # Both roles use suggested
        assert 'Architected cloud-native microservices' in result
        assert 'Designed RESTful APIs' in result
        assert 'Implemented CI/CD pipelines with Jenkins' in result

    def test_pe_role_ordering_preserved(self):
        """PE roles appear in sequence (role_0 before role_1) in output."""
        comparison = make_comparison()
        approvals = make_all_approvals(comparison)

        assembler = FinalAssembler()
        result = assembler.assemble(comparison, approvals)

        pos_role_0 = result.find('Acme Corp')
        pos_role_1 = result.find('Beta Inc')
        assert pos_role_0 < pos_role_1, "role_0 should appear before role_1"
