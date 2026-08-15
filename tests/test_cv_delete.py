"""Unit tests for DELETE /api/applications/<app_id>/cv endpoint.

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 5.3, 5.4, 5.5, 5.6
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Create a Flask test client with mocked AWS services."""
    with patch('backend.boto3') as mock_boto3, \
         patch('backend.s3_client') as mock_s3, \
         patch('backend.applications_table') as mock_table:
        # Ensure S3 is marked as available
        with patch('backend.S3_AVAILABLE', True):
            from backend import app
            app.config['TESTING'] = True
            with app.test_client() as client:
                yield client


@pytest.fixture
def mock_s3():
    """Provide a mock S3 client."""
    with patch('backend.s3_client') as mock:
        yield mock


@pytest.fixture
def mock_table():
    """Provide a mock DynamoDB applications table."""
    with patch('backend.applications_table') as mock:
        yield mock


@pytest.fixture
def sample_app_with_cv():
    """Sample DynamoDB application record that has a CV attached."""
    return {
        'Item': {
            'userId': 'user123',
            'id': 'app456',
            'company': 'Acme Corp',
            'role': 'Engineer',
            'cvS3Key': 'user123/app456/resume.pdf',
            'cvFilename': 'resume.pdf',
        }
    }


@pytest.fixture
def sample_app_without_cv():
    """Sample DynamoDB application record with no CV."""
    return {
        'Item': {
            'userId': 'user123',
            'id': 'app456',
            'company': 'Acme Corp',
            'role': 'Engineer',
        }
    }


class TestDeleteCVSuccess:
    """Tests for successful CV deletion (Requirements 3.1, 3.2, 5.3)."""

    def test_successful_deletion_removes_s3_object_and_dynamodb_metadata(
        self, mock_s3, mock_table, sample_app_with_cv
    ):
        """Successful delete removes S3 object and clears DynamoDB CV metadata."""
        with patch('backend.S3_AVAILABLE', True):
            from backend import app
            app.config['TESTING'] = True

            mock_table.get_item.return_value = sample_app_with_cv
            mock_s3.delete_object.return_value = {}
            mock_table.update_item.return_value = {}

            with app.test_client() as client:
                response = client.delete(
                    '/api/applications/app456/cv?userId=user123'
                )

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'

            # Verify S3 delete was called with correct bucket and key
            mock_s3.delete_object.assert_called_once_with(
                Bucket='careerops-589535355002',
                Key='user123/app456/resume.pdf'
            )

            # Verify DynamoDB update removed CV metadata
            mock_table.update_item.assert_called_once_with(
                Key={'userId': 'user123', 'id': 'app456'},
                UpdateExpression='REMOVE cvS3Key, cvFilename'
            )


class TestDeleteCVNotFound:
    """Tests for 404 when no CV is associated (Requirement 3.4, 5.6)."""

    def test_404_when_no_cv_associated_with_application(
        self, mock_s3, mock_table, sample_app_without_cv
    ):
        """Returns 404 when application has no CV metadata."""
        with patch('backend.S3_AVAILABLE', True):
            from backend import app
            app.config['TESTING'] = True

            mock_table.get_item.return_value = sample_app_without_cv

            with app.test_client() as client:
                response = client.delete(
                    '/api/applications/app456/cv?userId=user123'
                )

            assert response.status_code == 404
            data = response.get_json()
            assert 'No CV' in data['error'] or 'no' in data['error'].lower()

    def test_404_when_application_not_found(self, mock_s3, mock_table):
        """Returns 404 when the application doesn't exist in DynamoDB."""
        with patch('backend.S3_AVAILABLE', True):
            from backend import app
            app.config['TESTING'] = True

            mock_table.get_item.return_value = {}  # No Item key

            with app.test_client() as client:
                response = client.delete(
                    '/api/applications/nonexistent/cv?userId=user123'
                )

            assert response.status_code == 404
            data = response.get_json()
            assert 'not found' in data['error'].lower()


class TestDeleteCVS3Failure:
    """Tests for 503 when S3 deletion fails (Requirement 3.3, 5.4)."""

    def test_503_when_s3_deletion_fails_dynamodb_unchanged(
        self, mock_s3, mock_table, sample_app_with_cv
    ):
        """Returns 503 when S3 delete_object raises and DynamoDB stays unchanged."""
        with patch('backend.S3_AVAILABLE', True):
            from backend import app
            app.config['TESTING'] = True

            mock_table.get_item.return_value = sample_app_with_cv
            mock_s3.delete_object.side_effect = Exception('S3 service error')

            with app.test_client() as client:
                response = client.delete(
                    '/api/applications/app456/cv?userId=user123'
                )

            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data

            # DynamoDB should NOT have been updated
            mock_table.update_item.assert_not_called()

    def test_503_when_s3_unavailable(self, mock_s3, mock_table):
        """Returns 503 when S3_AVAILABLE is False."""
        with patch('backend.S3_AVAILABLE', False):
            from backend import app
            app.config['TESTING'] = True

            with app.test_client() as client:
                response = client.delete(
                    '/api/applications/app456/cv?userId=user123'
                )

            assert response.status_code == 503
            data = response.get_json()
            assert 'unavailable' in data['error'].lower() or 'storage' in data['error'].lower()


class TestDeleteCVPartialFailure:
    """Tests for 500 partial failure: S3 succeeds but DynamoDB fails (Requirement 3.5)."""

    def test_500_partial_failure_s3_succeeds_dynamodb_update_fails(
        self, mock_s3, mock_table, sample_app_with_cv
    ):
        """Returns 500 when S3 deletion succeeds but DynamoDB metadata removal fails."""
        with patch('backend.S3_AVAILABLE', True):
            from backend import app
            app.config['TESTING'] = True

            mock_table.get_item.return_value = sample_app_with_cv
            mock_s3.delete_object.return_value = {}
            mock_table.update_item.side_effect = Exception('DynamoDB write error')

            with app.test_client() as client:
                response = client.delete(
                    '/api/applications/app456/cv?userId=user123'
                )

            assert response.status_code == 500
            data = response.get_json()
            assert 'partial' in data['error'].lower() or 'Partial' in data['error']

            # S3 delete was still called
            mock_s3.delete_object.assert_called_once()


class TestDeleteCVPermissions:
    """Tests for 403 userId mismatch (Requirement 5.5)."""

    def test_403_for_userid_mismatch(self, mock_s3, mock_table):
        """Returns 403 when requesting userId doesn't match the application owner."""
        with patch('backend.S3_AVAILABLE', True):
            from backend import app
            app.config['TESTING'] = True

            # The app belongs to 'user123' but the request comes from 'attacker'
            mock_table.get_item.return_value = {
                'Item': {
                    'userId': 'user123',
                    'id': 'app456',
                    'company': 'Acme Corp',
                    'cvS3Key': 'user123/app456/resume.pdf',
                    'cvFilename': 'resume.pdf',
                }
            }

            with app.test_client() as client:
                response = client.delete(
                    '/api/applications/app456/cv?userId=attacker'
                )

            # Backend checks userId ownership and returns 403 when mismatch
            assert response.status_code == 403

    def test_400_when_userid_missing(self, mock_s3, mock_table):
        """Returns 400 when userId query parameter is not provided."""
        with patch('backend.S3_AVAILABLE', True):
            from backend import app
            app.config['TESTING'] = True

            with app.test_client() as client:
                response = client.delete('/api/applications/app456/cv')

            assert response.status_code == 400
            data = response.get_json()
            assert 'userId' in data['error']
