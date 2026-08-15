"""Unit tests for the CV download endpoint (GET /api/applications/<app_id>/cv)."""

import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Create a Flask test client with mocked AWS services."""
    with patch('backend.boto3') as mock_boto3, \
         patch('backend.S3_AVAILABLE', True):
        # Mock DynamoDB resource
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb

        # Mock S3 client
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        import importlib
        import backend
        importlib.reload(backend)

        backend.S3_AVAILABLE = True
        backend.s3_client = mock_s3
        backend.applications_table = mock_table

        app = backend.app
        app.config['TESTING'] = True

        with app.test_client() as test_client:
            test_client._mock_s3 = mock_s3
            test_client._mock_table = mock_table
            yield test_client


class TestCVDownloadSuccess:
    """Test successful CV download returns pre-signed URL."""

    def test_successful_download_returns_presigned_url(self, client):
        """Validates: Requirements 2.1, 2.2, 5.2"""
        client._mock_table.get_item.return_value = {
            'Item': {
                'userId': 'user123',
                'id': 'app456',
                'cvS3Key': 'user123/app456/resume.pdf',
                'cvFilename': 'resume.pdf'
            }
        }
        client._mock_s3.generate_presigned_url.return_value = (
            'https://careerops-589535355002.s3.amazonaws.com/user123/app456/resume.pdf?signed'
        )

        response = client.get('/api/applications/app456/cv?userId=user123')

        assert response.status_code == 200
        data = response.get_json()
        assert 'url' in data
        assert 'filename' in data
        assert data['filename'] == 'resume.pdf'
        assert data['url'].startswith('https://')

    def test_presigned_url_generated_with_correct_params(self, client):
        """Validates: Requirements 2.1, 2.2"""
        client._mock_table.get_item.return_value = {
            'Item': {
                'userId': 'user123',
                'id': 'app456',
                'cvS3Key': 'user123/app456/resume.pdf',
                'cvFilename': 'resume.pdf'
            }
        }
        client._mock_s3.generate_presigned_url.return_value = 'https://signed-url'

        client.get('/api/applications/app456/cv?userId=user123')

        client._mock_s3.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={'Bucket': 'careerops-589535355002', 'Key': 'user123/app456/resume.pdf'},
            ExpiresIn=900
        )


class TestCVDownloadNoCVMetadata:
    """Test 404 when no CV metadata exists on the application record."""

    def test_404_when_no_cv_s3key(self, client):
        """Validates: Requirements 2.3"""
        client._mock_table.get_item.return_value = {
            'Item': {
                'userId': 'user123',
                'id': 'app456'
                # No cvS3Key or cvFilename
            }
        }

        response = client.get('/api/applications/app456/cv?userId=user123')

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'No CV' in data['error'] or 'no CV' in data['error'].lower()

    def test_404_when_cv_fields_are_empty(self, client):
        """Validates: Requirements 2.3"""
        client._mock_table.get_item.return_value = {
            'Item': {
                'userId': 'user123',
                'id': 'app456',
                'cvS3Key': '',
                'cvFilename': ''
            }
        }

        response = client.get('/api/applications/app456/cv?userId=user123')

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data


class TestCVDownloadS3NoSuchKey:
    """Test 404 when S3 object doesn't exist (NoSuchKey)."""

    def test_404_when_s3_raises_no_such_key_exception(self, client):
        """Validates: Requirements 2.5"""
        client._mock_table.get_item.return_value = {
            'Item': {
                'userId': 'user123',
                'id': 'app456',
                'cvS3Key': 'user123/app456/resume.pdf',
                'cvFilename': 'resume.pdf'
            }
        }
        # Simulate NoSuchKey via the exceptions attribute
        no_such_key_error = type('NoSuchKey', (Exception,), {})()
        client._mock_s3.exceptions.NoSuchKey = type('NoSuchKey', (Exception,), {})
        client._mock_s3.generate_presigned_url.side_effect = client._mock_s3.exceptions.NoSuchKey()

        response = client.get('/api/applications/app456/cv?userId=user123')

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()

    def test_404_when_s3_error_contains_nosuchkey_string(self, client):
        """Validates: Requirements 2.5"""
        client._mock_table.get_item.return_value = {
            'Item': {
                'userId': 'user123',
                'id': 'app456',
                'cvS3Key': 'user123/app456/resume.pdf',
                'cvFilename': 'resume.pdf'
            }
        }
        # Simulate a generic exception containing 'NoSuchKey' in its message
        client._mock_s3.exceptions.NoSuchKey = type('NoSuchKey', (Exception,), {})
        client._mock_s3.generate_presigned_url.side_effect = Exception(
            'An error occurred (NoSuchKey) when calling the GetObject operation'
        )

        response = client.get('/api/applications/app456/cv?userId=user123')

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()


class TestCVDownloadS3ServiceError:
    """Test 503 for S3 service errors."""

    def test_503_when_s3_unavailable(self, client):
        """Validates: Requirements 2.4, 5.4"""
        import backend
        backend.S3_AVAILABLE = False

        response = client.get('/api/applications/app456/cv?userId=user123')

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
        assert 'unavailable' in data['error'].lower() or 'service' in data['error'].lower()

    def test_503_when_generate_presigned_url_fails(self, client):
        """Validates: Requirements 2.4"""
        client._mock_table.get_item.return_value = {
            'Item': {
                'userId': 'user123',
                'id': 'app456',
                'cvS3Key': 'user123/app456/resume.pdf',
                'cvFilename': 'resume.pdf'
            }
        }
        # Simulate a generic S3 service error (not NoSuchKey)
        client._mock_s3.exceptions.NoSuchKey = type('NoSuchKey', (Exception,), {})
        client._mock_s3.generate_presigned_url.side_effect = Exception('Internal S3 error')

        response = client.get('/api/applications/app456/cv?userId=user123')

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data


class TestCVDownloadUserIdMismatch:
    """Test 403 for userId mismatch."""

    def test_404_when_application_not_found(self, client):
        """Validates: Requirements 5.6"""
        client._mock_table.get_item.return_value = {}  # No 'Item' key

        response = client.get('/api/applications/app456/cv?userId=user123')

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()

    def test_400_when_user_id_missing(self, client):
        """Validates: Requirements 5.5"""
        response = client.get('/api/applications/app456/cv')

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'userId' in data['error']
