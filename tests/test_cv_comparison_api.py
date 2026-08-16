"""Unit tests for POST /api/compare-cv and POST /api/assemble-cv endpoints."""

import sys
sys.path.insert(0, '/Users/navinkumar/workrepos/pers-prj/careerops')

import json
import pytest
from unittest.mock import MagicMock, patch
import backend


# ========== SAMPLE CV CONSTANT ==========

SAMPLE_CV = """# Jane Doe

**Senior Cloud Infrastructure Engineer**

jane.doe@email.com | +1-555-123-4567 | linkedin.com/in/janedoe | github.com/janedoe

## PROFESSIONAL SUMMARY

Results-driven Cloud Infrastructure Engineer with 10+ years of experience designing, deploying, and managing scalable distributed systems on AWS and GCP. Proven track record in reducing infrastructure costs by 40% while improving system uptime to 99.99%.

## CORE SKILLS

- Cloud Platforms: AWS (EC2, ECS, Lambda, S3, RDS, DynamoDB), GCP (GKE, Cloud Run)
- Infrastructure as Code: Terraform, CloudFormation, Pulumi
- Containers & Orchestration: Docker, Kubernetes, Helm, ArgoCD
- CI/CD: GitHub Actions, Jenkins, GitLab CI, CodePipeline
- Monitoring: Datadog, Prometheus, Grafana, CloudWatch
- Programming: Python, Go, Bash, TypeScript

## PROFESSIONAL EXPERIENCE

### Lead Cloud Engineer — Acme Corp

**January 2021 – Present | San Francisco, CA**

- Architected multi-region Kubernetes platform serving 50M+ daily requests with 99.99% uptime
- Reduced cloud spend by $2.4M annually through reserved instance optimization and spot fleet management
- Led migration of 200+ microservices from EC2 to EKS, achieving 60% improvement in deployment velocity
- Established SRE practices including SLOs, error budgets, and automated incident response

### Senior DevOps Engineer — TechStart Inc

**March 2018 – December 2020 | Austin, TX**

- Designed and implemented CI/CD pipelines reducing release cycle from 2 weeks to 2 hours
- Built self-service infrastructure provisioning platform used by 80+ developers
- Implemented infrastructure drift detection saving 20+ hours per week in manual reconciliation

## CERTIFICATIONS

- AWS Solutions Architect Professional (SAP-C02) — 2024
- Certified Kubernetes Administrator (CKA) — 2023
- HashiCorp Terraform Associate — 2022
- AWS DevOps Engineer Professional — 2021

## EDUCATION

- M.S. Computer Science — Stanford University, 2014
- B.S. Computer Engineering — University of Texas at Austin, 2012

## COMMUNITY LEADERSHIP & ENGAGEMENT

- Conference Speaker: KubeCon NA 2023, AWS re:Invent 2022, DevOpsDays Austin 2021
- Open Source Maintainer: terraform-aws-eks-blueprint (2.1k stars)
- Technical Blogger: 50+ articles on cloud architecture (120k monthly readers)
- Mentor: Cloud Native Computing Foundation mentorship program (6 mentees)

## LANGUAGES

- English (Native)
- Spanish (Professional Working Proficiency)
- Mandarin (Conversational)
"""

SAMPLE_TAILORED_CV = """# Jane Doe

**Senior Cloud Infrastructure Engineer & Platform Architect**

jane.doe@email.com | +1-555-123-4567 | linkedin.com/in/janedoe | github.com/janedoe

## PROFESSIONAL SUMMARY

Results-driven Cloud Infrastructure Engineer with 10+ years of experience designing, deploying, and managing scalable distributed systems on AWS and GCP. Expert in Kubernetes orchestration, infrastructure automation, and cost optimization. Proven track record in reducing infrastructure costs by 40% while improving system uptime to 99.99%.

## CORE SKILLS

- Cloud Platforms: AWS (EC2, ECS, Lambda, S3, RDS, DynamoDB, EKS), GCP (GKE, Cloud Run)
- Infrastructure as Code: Terraform, CloudFormation, Pulumi, CDK
- Containers & Orchestration: Docker, Kubernetes, Helm, ArgoCD, Istio
- CI/CD: GitHub Actions, Jenkins, GitLab CI, CodePipeline, ArgoCD
- Monitoring & Observability: Datadog, Prometheus, Grafana, CloudWatch, OpenTelemetry
- Programming: Python, Go, Bash, TypeScript

## PROFESSIONAL EXPERIENCE

### Lead Cloud Engineer — Acme Corp

**January 2021 – Present | San Francisco, CA**

- Architected multi-region Kubernetes platform serving 50M+ daily requests with 99.99% uptime
- Reduced cloud spend by $2.4M annually through reserved instance optimization and spot fleet management
- Led migration of 200+ microservices from EC2 to EKS, achieving 60% improvement in deployment velocity
- Established SRE practices including SLOs, error budgets, and automated incident response
- Implemented service mesh with Istio for zero-trust networking across 200+ microservices

### Senior DevOps Engineer — TechStart Inc

**March 2018 – December 2020 | Austin, TX**

- Designed and implemented CI/CD pipelines reducing release cycle from 2 weeks to 2 hours
- Built self-service infrastructure provisioning platform used by 80+ developers
- Implemented infrastructure drift detection saving 20+ hours per week in manual reconciliation

## CERTIFICATIONS

- AWS Solutions Architect Professional (SAP-C02) — 2024
- Certified Kubernetes Administrator (CKA) — 2023
- HashiCorp Terraform Associate — 2022
- AWS DevOps Engineer Professional — 2021

## EDUCATION

- M.S. Computer Science — Stanford University, 2014
- B.S. Computer Engineering — University of Texas at Austin, 2012

## COMMUNITY LEADERSHIP & ENGAGEMENT

- Conference Speaker: KubeCon NA 2023, AWS re:Invent 2022, DevOpsDays Austin 2021
- Open Source Maintainer: terraform-aws-eks-blueprint (2.1k stars)
- Technical Blogger: 50+ articles on cloud architecture (120k monthly readers)
- Mentor: Cloud Native Computing Foundation mentorship program (6 mentees)

## LANGUAGES

- English (Native)
- Spanish (Professional Working Proficiency)
- Mandarin (Conversational)
"""


# ========== FIXTURES ==========

@pytest.fixture
def client():
    """Create a Flask test client with mocked DynamoDB."""
    mock_table = MagicMock()
    mock_table.get_item.return_value = {'Item': None}
    mock_table.put_item.return_value = {}
    backend.applications_table = mock_table
    backend.DYNAMODB_AVAILABLE = True

    app = backend.app
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


# ========== /api/compare-cv TESTS ==========

class TestCompareCVHappyPath:
    """Test /api/compare-cv happy path with valid CVs."""

    def test_returns_200_with_expected_keys(self, client):
        """Happy path: valid CVs return 200 with comparison, baseline_score, max_score, total_changes."""
        payload = {
            'userId': 'user1',
            'appId': 'app1',
            'originalCv': SAMPLE_CV,
            'tailoredCv': SAMPLE_TAILORED_CV,
            'baselineScore': 65,
            'categoryScores': {
                'subheading': 2,
                'summary': 5,
                'core_skills': 8,
                'professional_experience.role_0': 3,
            },
        }

        response = client.post(
            '/api/compare-cv',
            data=json.dumps(payload),
            content_type='application/json',
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'comparison' in data
        assert 'baseline_score' in data
        assert 'max_score' in data
        assert 'total_changes' in data

    def test_total_changes_counts_changed_entries(self, client):
        """total_changes equals the number of comparison entries where changed=True."""
        payload = {
            'userId': 'user1',
            'appId': 'app1',
            'originalCv': SAMPLE_CV,
            'tailoredCv': SAMPLE_TAILORED_CV,
            'baselineScore': 65,
            'categoryScores': {},
        }

        response = client.post(
            '/api/compare-cv',
            data=json.dumps(payload),
            content_type='application/json',
        )

        assert response.status_code == 200
        data = response.get_json()
        comparison = data['comparison']
        expected_changes = sum(1 for entry in comparison.values() if entry['changed'])
        assert data['total_changes'] == expected_changes
        # We know the tailored CV differs in at least subheading, summary, core_skills, and role_0
        assert data['total_changes'] >= 3


class TestCompareCVEmptyOriginal:
    """Test /api/compare-cv with empty originalCv returns 400."""

    def test_empty_original_cv_returns_400(self, client):
        """Empty originalCv should result in a 400 parse error."""
        payload = {
            'userId': 'user1',
            'appId': 'app1',
            'originalCv': '',
            'tailoredCv': SAMPLE_TAILORED_CV,
            'baselineScore': 65,
            'categoryScores': {},
        }

        response = client.post(
            '/api/compare-cv',
            data=json.dumps(payload),
            content_type='application/json',
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_whitespace_only_original_cv_returns_400(self, client):
        """Whitespace-only originalCv should also fail parsing."""
        payload = {
            'userId': 'user1',
            'appId': 'app1',
            'originalCv': '   \n\n  \t  ',
            'tailoredCv': SAMPLE_TAILORED_CV,
            'baselineScore': 65,
            'categoryScores': {},
        }

        response = client.post(
            '/api/compare-cv',
            data=json.dumps(payload),
            content_type='application/json',
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestCompareCVNoHeaders:
    """Test /api/compare-cv with no recognizable headers returns 400."""

    def test_no_headers_returns_400(self, client):
        """CV text without any H1 or H2 headers should fail parsing."""
        payload = {
            'userId': 'user1',
            'appId': 'app1',
            'originalCv': 'Just some plain text without any markdown headers or structure.',
            'tailoredCv': SAMPLE_TAILORED_CV,
            'baselineScore': 65,
            'categoryScores': {},
        }

        response = client.post(
            '/api/compare-cv',
            data=json.dumps(payload),
            content_type='application/json',
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'header' in data['error'].lower() or 'recognizable' in data['error'].lower()


class TestCompareCVScoreImpacts:
    """Test /api/compare-cv attaches score_impact from categoryScores correctly."""

    def test_score_impacts_attached_to_matching_categories(self, client):
        """categoryScores values should appear as score_impact on matching comparison entries."""
        category_scores = {
            'summary': 5,
            'core_skills': 8,
            'professional_experience.role_0': 3,
            'certifications': 0,
        }

        payload = {
            'userId': 'user1',
            'appId': 'app1',
            'originalCv': SAMPLE_CV,
            'tailoredCv': SAMPLE_TAILORED_CV,
            'baselineScore': 65,
            'categoryScores': category_scores,
        }

        response = client.post(
            '/api/compare-cv',
            data=json.dumps(payload),
            content_type='application/json',
        )

        assert response.status_code == 200
        data = response.get_json()
        comparison = data['comparison']

        # Verify each specified category has the correct score_impact
        assert comparison['summary']['score_impact'] == 5
        assert comparison['core_skills']['score_impact'] == 8
        assert comparison['professional_experience.role_0']['score_impact'] == 3
        assert comparison['certifications']['score_impact'] == 0

    def test_unspecified_categories_have_zero_score_impact(self, client):
        """Categories not in categoryScores should have score_impact=0."""
        payload = {
            'userId': 'user1',
            'appId': 'app1',
            'originalCv': SAMPLE_CV,
            'tailoredCv': SAMPLE_TAILORED_CV,
            'baselineScore': 65,
            'categoryScores': {'summary': 10},
        }

        response = client.post(
            '/api/compare-cv',
            data=json.dumps(payload),
            content_type='application/json',
        )

        assert response.status_code == 200
        data = response.get_json()
        comparison = data['comparison']

        # Categories not mentioned in categoryScores should remain at default 0
        assert comparison['heading']['score_impact'] == 0
        assert comparison['contact']['score_impact'] == 0
        assert comparison['languages']['score_impact'] == 0


# ========== /api/assemble-cv TESTS ==========

def _build_comparison_payload():
    """Helper: build a comparison dict from the two sample CVs using real parser/engine."""
    parser = backend.CVParser()
    original_parsed = parser.parse(SAMPLE_CV)
    tailored_parsed = parser.parse(SAMPLE_TAILORED_CV)
    engine = backend.ComparisonEngine()
    comparison = engine.compare(original_parsed, tailored_parsed)
    return comparison


class TestAssembleCVHappyPath:
    """Test /api/assemble-cv happy path."""

    def test_returns_200_with_assembled_cv_and_final_score(self, client):
        """Happy path: valid comparison and at least one approval returns 200."""
        comparison = _build_comparison_payload()

        # Approve summary and core_skills
        approvals = {key: False for key in comparison}
        approvals['summary'] = True
        approvals['core_skills'] = True

        # Add score_impact to comparison entries
        comparison['summary']['score_impact'] = 5
        comparison['core_skills']['score_impact'] = 8

        payload = {
            'userId': 'user1',
            'appId': 'app1',
            'comparison': comparison,
            'approvals': approvals,
            'baselineScore': 65,
            'categoryScores': {'summary': 5, 'core_skills': 8},
        }

        response = client.post(
            '/api/assemble-cv',
            data=json.dumps(payload),
            content_type='application/json',
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'assembled_cv' in data
        assert isinstance(data['assembled_cv'], str)
        assert len(data['assembled_cv']) > 0
        assert 'final_score' in data
        assert isinstance(data['final_score'], int)


class TestAssembleCVZeroApprovals:
    """Test /api/assemble-cv with zero approvals returns 400."""

    def test_empty_approvals_dict_returns_400(self, client):
        """Empty approvals dict should trigger AssemblyError -> 400."""
        comparison = _build_comparison_payload()

        payload = {
            'userId': 'user1',
            'appId': 'app1',
            'comparison': comparison,
            'approvals': {},
            'baselineScore': 65,
            'categoryScores': {},
        }

        response = client.post(
            '/api/assemble-cv',
            data=json.dumps(payload),
            content_type='application/json',
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestAssembleCVAllFalseApprovals:
    """Test /api/assemble-cv with all False approvals returns 400."""

    def test_all_false_approvals_returns_400(self, client):
        """All approvals set to False should trigger AssemblyError -> 400."""
        comparison = _build_comparison_payload()

        approvals = {key: False for key in comparison}

        payload = {
            'userId': 'user1',
            'appId': 'app1',
            'comparison': comparison,
            'approvals': approvals,
            'baselineScore': 65,
            'categoryScores': {},
        }

        response = client.post(
            '/api/assemble-cv',
            data=json.dumps(payload),
            content_type='application/json',
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'approved' in data['error'].lower() or 'at least one' in data['error'].lower()


class TestAssembleCVUsesSuggestedContent:
    """Test /api/assemble-cv uses suggested content for approved categories."""

    def test_approved_category_uses_suggested_content(self, client):
        """When a category is approved, its suggested_content should appear in assembled_cv."""
        comparison = _build_comparison_payload()

        # The tailored CV has a different subheading
        # Original: "**Senior Cloud Infrastructure Engineer**"
        # Tailored: "**Senior Cloud Infrastructure Engineer & Platform Architect**"

        approvals = {key: False for key in comparison}
        approvals['subheading'] = True  # Approve the changed subheading

        payload = {
            'userId': 'user1',
            'appId': 'app1',
            'comparison': comparison,
            'approvals': approvals,
            'baselineScore': 65,
            'categoryScores': {},
        }

        response = client.post(
            '/api/assemble-cv',
            data=json.dumps(payload),
            content_type='application/json',
        )

        assert response.status_code == 200
        data = response.get_json()
        assembled = data['assembled_cv']

        # The suggested subheading should be present
        assert 'Platform Architect' in assembled

    def test_unapproved_category_uses_original_content(self, client):
        """When a category is NOT approved, original_content should appear in assembled_cv."""
        comparison = _build_comparison_payload()

        # Approve only heading (which is unchanged) - we need at least one True
        approvals = {key: False for key in comparison}
        approvals['heading'] = True  # heading is unchanged, so this works

        payload = {
            'userId': 'user1',
            'appId': 'app1',
            'comparison': comparison,
            'approvals': approvals,
            'baselineScore': 65,
            'categoryScores': {},
        }

        response = client.post(
            '/api/assemble-cv',
            data=json.dumps(payload),
            content_type='application/json',
        )

        assert response.status_code == 200
        data = response.get_json()
        assembled = data['assembled_cv']

        # subheading NOT approved → original content used (no "Platform Architect")
        assert 'Platform Architect' not in assembled
        # Original subheading should be there
        assert 'Senior Cloud Infrastructure Engineer' in assembled
