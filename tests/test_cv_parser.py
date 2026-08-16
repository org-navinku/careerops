"""Unit tests for CVParser edge cases."""
import sys
sys.path.insert(0, '/Users/navinkumar/workrepos/pers-prj/careerops')

import re
import pytest
import backend
from backend import CVParser, ParseError


@pytest.fixture
def parser():
    return CVParser()


KNOWN_CV = """\
# Jane Doe

**Senior Software Engineer**

jane.doe@example.com | 555-123-4567 | San Francisco, CA

## Professional Summary
- 10 years of experience in backend systems
- Expert in distributed computing

## Core Skills
- Python, Go, Rust
- Kubernetes, Docker, Terraform

## Professional Experience

### Lead Engineer at TechCorp
**Jan 2020 - Present**

- Designed microservices architecture
- Led team of 8 engineers

### Software Engineer at StartupXYZ
**Mar 2016 - Dec 2019**

- Built real-time data pipeline
- Reduced latency by 40%

## Certifications
- AWS Solutions Architect Professional
- Certified Kubernetes Administrator

## Education
- MSc Computer Science, Stanford University, 2016
- BSc Mathematics, UC Berkeley, 2014

## Community Leadership & Engagement
- Organizer, Bay Area Python Meetup
- Speaker at KubeCon 2022

## Languages
- English (Native)
- Spanish (Conversational)
"""


class TestCVParserEmpty:
    """Test empty input raises ParseError."""

    def test_empty_string(self, parser):
        with pytest.raises(backend.ParseError):
            parser.parse("")

    def test_whitespace_only(self, parser):
        with pytest.raises(backend.ParseError):
            parser.parse("   \n\n  \t  ")

    def test_none_input(self, parser):
        with pytest.raises((backend.ParseError, TypeError, AttributeError)):
            parser.parse(None)


class TestCVParserNoHeaders:
    """Test input with no recognizable headers raises ParseError."""

    def test_random_text(self, parser):
        with pytest.raises(backend.ParseError):
            parser.parse("This is just some random text\nwithout any markdown headers.")

    def test_bullet_list_only(self, parser):
        with pytest.raises(backend.ParseError):
            parser.parse("- item one\n- item two\n- item three")

    def test_bold_text_only(self, parser):
        with pytest.raises(backend.ParseError):
            parser.parse("**Bold text**\nSome content\n**More bold**")


class TestCVParserMissingOptionalSections:
    """Test CV with missing optional sections parses successfully."""

    def test_no_languages(self, parser):
        """CV without Languages section should still parse."""
        cv = """\
# John Smith

**DevOps Engineer**

john@test.com | 555-000-1234 | NYC

## Professional Summary
- Experienced DevOps engineer

## Core Skills
- AWS, Terraform, Ansible

## Professional Experience

### DevOps Lead at CloudInc
**2021 - Present**

- Managed cloud infrastructure

## Certifications
- AWS Certified

## Education
- BSc CS, MIT, 2018

## Community Leadership & Engagement
- Open source contributor
"""
        result = parser.parse(cv)
        assert 'heading' in result
        assert 'summary' in result
        assert 'professional_experience' in result
        assert 'languages' not in result

    def test_no_certifications_or_community(self, parser):
        """CV with only core sections should parse."""
        cv = """\
# Alice Johnson

**Data Scientist**

alice@data.io | 555-999-8888 | London

## Professional Summary
- ML specialist with 5 years experience

## Core Skills
- Python, TensorFlow, PyTorch

## Professional Experience

### Data Scientist at BigDataCo
**2019 - Present**

- Built recommendation models

## Education
- PhD Machine Learning, Oxford, 2019
"""
        result = parser.parse(cv)
        assert 'heading' in result
        assert 'professional_experience' in result
        assert 'certifications' not in result
        assert 'community' not in result
        assert 'languages' not in result

    def test_heading_only(self, parser):
        """CV with just H1 heading should parse (has recognizable structure)."""
        cv = "# Minimal Person\n\nSome content here\n"
        result = parser.parse(cv)
        assert 'heading' in result
        assert '# Minimal Person' in result['heading']


class TestCVParserMalformedH3:
    """Test malformed H3 headers in Professional Experience."""

    def test_h3_without_content(self, parser):
        """H3 role with no bullet points should still parse."""
        cv = """\
# Test User

**Engineer**

test@mail.com | 555-111-2222 | Remote

## Professional Experience

### Empty Role at SomeCo
**2022 - Present**

### Another Role at AnotherCo
**2020 - 2022**

- Did some work

## Education
- BSc, University, 2019
"""
        result = parser.parse(cv)
        pe = result['professional_experience']
        assert len(pe['roles']) == 2
        # First role has no content
        assert pe['roles'][0]['content'] == ''
        # Second role has content
        assert 'Did some work' in pe['roles'][1]['content']

    def test_h3_with_no_metadata(self, parser):
        """H3 role without bold metadata line should still parse."""
        cv = """\
# Test User

**Engineer**

test@mail.com | 555-111-2222 | Remote

## Professional Experience

### Solo Role at NoCo
- Immediate bullet point content
- More content

## Education
- BSc, University, 2019
"""
        result = parser.parse(cv)
        pe = result['professional_experience']
        assert len(pe['roles']) == 1
        assert pe['roles'][0]['metadata'] == ''
        assert 'Immediate bullet point' in pe['roles'][0]['content']


class TestCVParserExtraWhitespace:
    """Test CV with extra whitespace between sections."""

    def test_extra_blank_lines(self, parser):
        """Multiple blank lines between sections should not break parsing."""
        cv = """\
# Spacey Person



**Title With Gaps**



spacey@mail.com | 555-000-0000 | Nowhere



## Professional Summary



- Some summary content



## Core Skills



- Skill A
- Skill B



## Professional Experience



### Role at Company
**2020 - Present**



- Did things



## Education



- Degree, School, Year
"""
        result = parser.parse(cv)
        assert result['heading'] == '# Spacey Person'
        assert result['subheading'] == '**Title With Gaps**'
        assert 'spacey@mail.com' in result['contact']
        assert 'summary' in result
        assert 'core_skills' in result
        pe = result['professional_experience']
        assert len(pe['roles']) == 1


class TestCVParserRoundTrip:
    """Test parse + serialize round trip on a known CV."""

    def test_known_cv_round_trip(self, parser):
        """Parse and serialize should produce stable output after one pass."""
        categories = parser.parse(KNOWN_CV)
        serialized = parser.serialize(categories)

        # Re-parse and re-serialize should be identical
        re_categories = parser.parse(serialized)
        re_serialized = parser.serialize(re_categories)

        assert serialized == re_serialized

    def test_known_cv_preserves_content(self, parser):
        """All meaningful content should survive the round trip."""
        categories = parser.parse(KNOWN_CV)
        serialized = parser.serialize(categories)

        # Key content should still be present
        assert 'Jane Doe' in serialized
        assert 'Senior Software Engineer' in serialized
        assert 'jane.doe@example.com' in serialized
        assert 'Lead Engineer at TechCorp' in serialized
        assert 'Software Engineer at StartupXYZ' in serialized
        assert 'AWS Solutions Architect Professional' in serialized
        assert 'Stanford University' in serialized
        assert 'Bay Area Python Meetup' in serialized
        assert 'English (Native)' in serialized

    def test_known_cv_category_structure(self, parser):
        """Known CV should parse into expected structure."""
        categories = parser.parse(KNOWN_CV)

        assert categories['heading'] == '# Jane Doe'
        assert categories['subheading'] == '**Senior Software Engineer**'
        assert 'jane.doe@example.com' in categories['contact']
        assert '555-123-4567' in categories['contact']

        pe = categories['professional_experience']
        assert isinstance(pe, dict)
        assert len(pe['roles']) == 2
        assert 'Lead Engineer at TechCorp' in pe['roles'][0]['title']
        assert 'Software Engineer at StartupXYZ' in pe['roles'][1]['title']
