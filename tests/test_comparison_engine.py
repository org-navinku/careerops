"""Unit tests for ComparisonEngine."""
import sys
sys.path.insert(0, '/Users/navinkumar/workrepos/pers-prj/careerops')

import pytest
import backend
from backend import ComparisonEngine, ComparisonError, CVParser


@pytest.fixture
def engine():
    """Create a ComparisonEngine instance."""
    return ComparisonEngine()


@pytest.fixture
def sample_parsed_cv():
    """Create a full sample parsed CV dict."""
    return {
        'heading': '# John Doe',
        'subheading': '**Senior Engineer | Python, AWS**',
        'contact': 'john@example.com | New York',
        'summary': '## PROFESSIONAL SUMMARY\n\nExperienced engineer with 10 years.',
        'core_skills': '## CORE SKILLS\n\nPython, AWS, Docker, Kubernetes',
        'professional_experience': {
            'header': '## PROFESSIONAL EXPERIENCE',
            'roles': [
                {
                    'key': 'role_0',
                    'title': '### Senior Engineer at Acme Corp',
                    'metadata': '**Jan 2020 - Present**',
                    'content': '- Led team of 5\n- Designed microservices architecture',
                },
                {
                    'key': 'role_1',
                    'title': '### Engineer at Startup Inc',
                    'metadata': '**Jun 2017 - Dec 2019**',
                    'content': '- Built REST APIs\n- Managed CI/CD pipelines',
                },
            ],
        },
        'certifications': '## CERTIFICATIONS\n\n- AWS Solutions Architect',
        'education': '## EDUCATION\n\n- BSc Computer Science, MIT',
        'community': '## COMMUNITY LEADERSHIP & ENGAGEMENT\n\n- Open source contributor',
        'languages': '## LANGUAGES\n\nEnglish, Spanish',
    }


class TestIdenticalCVs:
    """Test that identical parsed CVs produce zero changes."""

    def test_identical_cvs_no_changes(self, engine, sample_parsed_cv):
        """Identical CVs should produce no changed entries."""
        result = engine.compare(sample_parsed_cv, sample_parsed_cv)

        for key, entry in result.items():
            assert entry['changed'] is False, (
                f"Key '{key}' should not be marked changed for identical CVs"
            )
            assert entry['original_content'] == entry['suggested_content'], (
                f"Key '{key}': original and suggested should be identical"
            )
            assert entry['score_impact'] == 0

    def test_identical_minimal_cv(self, engine):
        """Minimal CV (heading only) compared to itself has no changes."""
        minimal = {'heading': '# Jane Smith'}
        result = engine.compare(minimal, minimal)

        assert result['heading']['changed'] is False
        assert result['heading']['original_content'] == '# Jane Smith'
        assert result['heading']['suggested_content'] == '# Jane Smith'


class TestWhitespaceOnly:
    """Test whitespace-only differences are classified as unchanged."""

    def test_trailing_whitespace_unchanged(self, engine, sample_parsed_cv):
        """Trailing whitespace in string categories should not count as a change."""
        modified = dict(sample_parsed_cv)
        modified['heading'] = '# John Doe   '
        modified['summary'] = sample_parsed_cv['summary'] + '  \n  '
        modified['core_skills'] = '  ' + sample_parsed_cv['core_skills'] + '\t'

        result = engine.compare(sample_parsed_cv, modified)

        assert result['heading']['changed'] is False
        assert result['summary']['changed'] is False
        assert result['core_skills']['changed'] is False

    def test_whitespace_only_pe_header(self, engine, sample_parsed_cv):
        """PE header with only whitespace differences is unchanged."""
        modified = dict(sample_parsed_cv)
        modified['professional_experience'] = {
            'header': '## PROFESSIONAL EXPERIENCE  ',
            'roles': sample_parsed_cv['professional_experience']['roles'],
        }

        result = engine.compare(sample_parsed_cv, modified)

        assert result['professional_experience']['changed'] is False

    def test_unchanged_suggested_equals_original(self, engine, sample_parsed_cv):
        """When unchanged, suggested_content equals original_content exactly."""
        modified = dict(sample_parsed_cv)
        modified['heading'] = '# John Doe\n'

        result = engine.compare(sample_parsed_cv, modified)

        assert result['heading']['changed'] is False
        # suggested_content should be the original, not the whitespace-padded version
        assert result['heading']['suggested_content'] == sample_parsed_cv['heading']


class TestNoneInput:
    """Test None input raises ComparisonError."""

    def test_none_original_raises(self, engine, sample_parsed_cv):
        """None as original input raises ComparisonError."""
        with pytest.raises(backend.ComparisonError):
            engine.compare(None, sample_parsed_cv)

    def test_none_suggested_raises(self, engine, sample_parsed_cv):
        """None as suggested input raises ComparisonError."""
        with pytest.raises(backend.ComparisonError):
            engine.compare(sample_parsed_cv, None)

    def test_both_none_raises(self, engine):
        """Both inputs None raises ComparisonError."""
        with pytest.raises(backend.ComparisonError):
            engine.compare(None, None)


class TestNonDictInput:
    """Test non-dict input raises ComparisonError."""

    def test_string_original_raises(self, engine, sample_parsed_cv):
        """String as original raises ComparisonError."""
        with pytest.raises(backend.ComparisonError):
            engine.compare("not a dict", sample_parsed_cv)

    def test_list_original_raises(self, engine, sample_parsed_cv):
        """List as original raises ComparisonError."""
        with pytest.raises(backend.ComparisonError):
            engine.compare(['heading', 'summary'], sample_parsed_cv)

    def test_int_suggested_raises(self, engine, sample_parsed_cv):
        """Integer as suggested raises ComparisonError."""
        with pytest.raises(backend.ComparisonError):
            engine.compare(sample_parsed_cv, 42)

    def test_tuple_suggested_raises(self, engine, sample_parsed_cv):
        """Tuple as suggested raises ComparisonError."""
        with pytest.raises(backend.ComparisonError):
            engine.compare(sample_parsed_cv, ('heading', 'value'))


class TestMissingHeading:
    """Test missing 'heading' raises ComparisonError."""

    def test_original_missing_heading_raises(self, engine, sample_parsed_cv):
        """Original without 'heading' key raises ComparisonError."""
        no_heading = dict(sample_parsed_cv)
        del no_heading['heading']

        with pytest.raises(backend.ComparisonError):
            engine.compare(no_heading, sample_parsed_cv)

    def test_suggested_missing_heading_raises(self, engine, sample_parsed_cv):
        """Suggested without 'heading' key raises ComparisonError."""
        no_heading = dict(sample_parsed_cv)
        del no_heading['heading']

        with pytest.raises(backend.ComparisonError):
            engine.compare(sample_parsed_cv, no_heading)

    def test_empty_dict_raises(self, engine, sample_parsed_cv):
        """Empty dict (missing heading) raises ComparisonError."""
        with pytest.raises(backend.ComparisonError):
            engine.compare({}, sample_parsed_cv)


class TestDifferentContent:
    """Test different content is marked changed with correct values."""

    def test_heading_change_detected(self, engine, sample_parsed_cv):
        """Different heading is marked as changed."""
        modified = dict(sample_parsed_cv)
        modified['heading'] = '# Jane Smith'

        result = engine.compare(sample_parsed_cv, modified)

        assert result['heading']['changed'] is True
        assert result['heading']['original_content'] == '# John Doe'
        assert result['heading']['suggested_content'] == '# Jane Smith'

    def test_summary_change_detected(self, engine, sample_parsed_cv):
        """Different summary is marked as changed with correct content."""
        modified = dict(sample_parsed_cv)
        modified['summary'] = '## PROFESSIONAL SUMMARY\n\nNew improved summary.'

        result = engine.compare(sample_parsed_cv, modified)

        assert result['summary']['changed'] is True
        assert result['summary']['original_content'] == sample_parsed_cv['summary']
        assert result['summary']['suggested_content'] == modified['summary']

    def test_pe_role_change_detected(self, engine, sample_parsed_cv):
        """Different PE role content is marked as changed."""
        modified = dict(sample_parsed_cv)
        new_roles = [
            {
                'key': 'role_0',
                'title': '### Lead Architect at Acme Corp',
                'metadata': '**Jan 2020 - Present**',
                'content': '- Architected cloud-native platform\n- Mentored junior engineers',
            },
            sample_parsed_cv['professional_experience']['roles'][1],
        ]
        modified['professional_experience'] = {
            'header': '## PROFESSIONAL EXPERIENCE',
            'roles': new_roles,
        }

        result = engine.compare(sample_parsed_cv, modified)

        # role_0 should be changed (different title and content)
        assert result['professional_experience.role_0']['changed'] is True
        # role_1 should be unchanged
        assert result['professional_experience.role_1']['changed'] is False

    def test_score_impact_defaults_to_zero(self, engine, sample_parsed_cv):
        """score_impact should always default to 0."""
        modified = dict(sample_parsed_cv)
        modified['heading'] = '# Different Name'

        result = engine.compare(sample_parsed_cv, modified)

        for key, entry in result.items():
            assert entry['score_impact'] == 0, (
                f"Key '{key}' score_impact should be 0, got {entry['score_impact']}"
            )

    def test_new_category_in_suggested_marked_changed(self, engine):
        """Category present only in suggested is marked as changed."""
        original = {'heading': '# Name'}
        suggested = {
            'heading': '# Name',
            'summary': '## PROFESSIONAL SUMMARY\n\nNew summary',
        }

        result = engine.compare(original, suggested)

        assert result['summary']['changed'] is True
        assert result['summary']['original_content'] == ''
        assert result['summary']['suggested_content'] == '## PROFESSIONAL SUMMARY\n\nNew summary'

    def test_category_only_in_original_marked_changed(self, engine):
        """Category present only in original (empty in suggested) is marked changed."""
        original = {
            'heading': '# Name',
            'languages': '## LANGUAGES\n\nEnglish, French',
        }
        suggested = {'heading': '# Name'}

        result = engine.compare(original, suggested)

        assert result['languages']['changed'] is True
        assert result['languages']['original_content'] == '## LANGUAGES\n\nEnglish, French'
        assert result['languages']['suggested_content'] == ''
