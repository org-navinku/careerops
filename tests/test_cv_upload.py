"""Unit tests for the CV upload endpoint (POST /api/applications/<app_id>/cv).

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 5.1, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3, 6.4
"""

import io
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def client():
    """Create a Flask test client with mocked AWS services."""
    import backend

    mock_s3 = MagicMock()
    mock_table = MagicMock()

    backend.S3_AVAILABLE = True
    backend.s3_client = mock_s3
    backend.applications_table = mock_table

    app = backend.app
    app.config['TESTING'] = True

    with app.test_client() as test_client:
        test_client._mock_s3 = mock_s3
        test_client._mock_table = mock_table
        yield test_client


@pytest.fixture
def sample_app_record():
    """Sample DynamoDB application record."""
    return {
        'Item': {
            'userId': 'user123',
            'id': 'app456',
            'company': 'Acme Corp',
            'role': 'Engineer',
        }
    }


class TestCVUploadValidation:
    """Tests for upload validation (Requirements 6.1, 6.2, 6.3, 6.4, 1.1, 1.2)."""

    def test_400_when_no_file_provided(self, client):
        """Validates: Requirements 6.4 - No file field in request."""
        response = client.post(
            '/api/applications/app456/cv',
            data={'userId': 'user123'},
            content_type='multipart/form-data'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'file' in data['error'].lower() or 'No file' in data['error']

    def test_400_when_wrong_extension_txt(self, client):
        """Validates: Requirements 6.1, 1.1 - Reject .txt file."""
        data = {
            'userId': 'user123',
            'file': (io.BytesIO(b'plain text'), 'resume.txt', 'text/plain')
        }

        response = client.post(
            '/api/applications/app456/cv',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'file type' in data['error'].lower() or 'format' in data['error'].lower()

    def test_400_when_wrong_extension_jpg(self, client):
        """Validates: Requirements 6.1, 1.1 - Reject .jpg file."""
        data = {
            'userId': 'user123',
            'file': (io.BytesIO(b'\xff\xd8\xff\xe0'), 'photo.jpg', 'image/jpeg')
        }

        response = client.post(
            '/api/applications/app456/cv',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_400_when_content_type_mismatch(self, client):
        """Validates: Requirements 6.2, 6.3 - PDF extension but wrong Content-Type."""
        data = {
            'userId': 'user123',
            'file': (io.BytesIO(b'fake content'), 'resume.pdf', 'text/plain')
        }

        response = client.post(
            '/api/applications/app456/cv',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Content-Type' in data['error'] or 'content' in data['error'].lower()

    def test_400_when_docx_content_type_mismatch(self, client):
        """Validates: Requirements 6.2, 6.3 - DOCX extension with PDF Content-Type."""
        data = {
            'userId': 'user123',
            'file': (io.BytesIO(b'fake content'), 'resume.docx', 'application/pdf')
        }

        response = client.post(
            '/api/applications/app456/cv',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Content-Type' in data['error']

    def test_400_when_file_exceeds_5mb(self, client):
        """Validates: Requirements 1.2 - Reject file larger than 5 MB."""
        large_content = b'x' * (5 * 1024 * 1024 + 1)  # Just over 5MB
        data = {
            'userId': 'user123',
            'file': (io.BytesIO(large_content), 'resume.pdf', 'application/pdf')
        }

        response = client.post(
            '/api/applications/app456/cv',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert '5 MB' in data['error'] or 'large' in data['error'].lower()

    def test_400_when_file_is_empty(self, client):
        """Validates: Requirements 6.4 - Reject empty file body."""
        data = {
            'userId': 'user123',
            'file': (io.BytesIO(b''), 'resume.pdf', 'application/pdf')
        }

        response = client.post(
            '/api/applications/app456/cv',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'empty' in data['error'].lower()

    def test_400_when_userid_missing(self, client):
        """Validates: Requirements 5.5 - userId is required."""
        data = {
            'file': (io.BytesIO(b'%PDF-1.4 content'), 'resume.pdf', 'application/pdf')
        }

        response = client.post(
            '/api/applications/app456/cv',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'userId' in data['error']


class TestCVUploadSuccess:
    """Tests for successful upload (Requirements 1.3, 1.4, 5.1)."""

    def test_successful_upload_stores_file_and_metadata(self, client, sample_app_record):
        """Validates: Requirements 1.3, 1.4, 5.1 - Successful upload stores file in S3 and updates DynamoDB."""
        client._mock_table.get_item.return_value = sample_app_record
        client._mock_s3.put_object.return_value = {}
        client._mock_table.update_item.return_value = {}

        data = {
            'userId': 'user123',
            'file': (io.BytesIO(b'%PDF-1.4 fake pdf content'), 'resume.pdf', 'application/pdf')
        }

        response = client.post(
            '/api/applications/app456/cv',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 200
        resp_data = response.get_json()
        assert resp_data['status'] == 'ok'
        assert resp_data['filename'] == 'resume.pdf'
        assert resp_data['s3Key'] == 'user123/app456/resume.pdf'

        # Verify S3 put_object was called with correct parameters
        client._mock_s3.put_object.assert_called_once()
        call_kwargs = client._mock_s3.put_object.call_args[1]
        assert call_kwargs['Bucket'] == 'careerops-589535355002'
        assert call_kwargs['Key'] == 'user123/app456/resume.pdf'
        assert call_kwargs['ContentType'] == 'application/pdf'

        # Verify DynamoDB was updated with CV metadata
        client._mock_table.update_item.assert_called_once_with(
            Key={'userId': 'user123', 'id': 'app456'},
            UpdateExpression='SET cvS3Key = :s3key, cvFilename = :fname',
            ExpressionAttributeValues={
                ':s3key': 'user123/app456/resume.pdf',
                ':fname': 'resume.pdf'
            }
        )

    def test_successful_upload_docx_file(self, client, sample_app_record):
        """Validates: Requirements 1.1, 1.3 - DOCX files are also accepted."""
        client._mock_table.get_item.return_value = sample_app_record
        client._mock_s3.put_object.return_value = {}
        client._mock_table.update_item.return_value = {}

        docx_content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        data = {
            'userId': 'user123',
            'file': (io.BytesIO(b'PK\x03\x04 fake docx'), 'cv.docx', docx_content_type)
        }

        response = client.post(
            '/api/applications/app456/cv',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 200
        resp_data = response.get_json()
        assert resp_data['status'] == 'ok'
        assert resp_data['filename'] == 'cv.docx'
        assert resp_data['s3Key'] == 'user123/app456/cv.docx'


class TestCVUploadAuthorization:
    """Tests for authorization and application lookup (Requirements 5.5, 5.6, 1.7)."""

    def test_404_when_userid_mismatch(self, client):
        """Validates: Requirements 5.5 - 404 when userId doesn't match application owner.

        Note: The implementation queries DynamoDB with Key={userId, id}. If the userId
        doesn't match, no item is found, resulting in 404. This is by design since
        DynamoDB composite key lookup inherently enforces ownership.
        """
        # DynamoDB won't find the item because key includes the wrong userId
        client._mock_table.get_item.return_value = {}  # No Item

        data = {
            'userId': 'attacker',
            'file': (io.BytesIO(b'%PDF-1.4 content'), 'resume.pdf', 'application/pdf')
        }

        response = client.post(
            '/api/applications/app456/cv',
            data=data,
            content_type='multipart/form-data'
        )

        # With composite key design, mismatched userId returns 404
        assert response.status_code == 404
        resp_data = response.get_json()
        assert 'error' in resp_data
        assert 'not found' in resp_data['error'].lower()

    def test_404_when_application_does_not_exist(self, client):
        """Validates: Requirements 1.7, 5.6 - Application not found in DynamoDB."""
        client._mock_table.get_item.return_value = {}  # No Item key

        data = {
            'userId': 'user123',
            'file': (io.BytesIO(b'%PDF-1.4 content'), 'resume.pdf', 'application/pdf')
        }

        response = client.post(
            '/api/applications/nonexistent/cv',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 404
        resp_data = response.get_json()
        assert 'error' in resp_data
        assert 'not found' in resp_data['error'].lower()

        # Verify S3 was NOT called (file should not be stored)
        client._mock_s3.put_object.assert_not_called()


class TestCVUploadS3Unavailable:
    """Tests for S3 unavailability (Requirements 5.4, 1.5)."""

    def test_503_when_s3_unavailable(self, client):
        """Validates: Requirements 5.4 - 503 when S3_AVAILABLE is False."""
        import backend
        backend.S3_AVAILABLE = False

        data = {
            'userId': 'user123',
            'file': (io.BytesIO(b'%PDF-1.4 content'), 'resume.pdf', 'application/pdf')
        }

        response = client.post(
            '/api/applications/app456/cv',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 503
        resp_data = response.get_json()
        assert 'error' in resp_data
        assert 'unavailable' in resp_data['error'].lower() or 'storage' in resp_data['error'].lower()

        # Restore for other tests
        backend.S3_AVAILABLE = True

    def test_503_when_s3_put_object_fails(self, client, sample_app_record):
        """Validates: Requirements 1.5 - 503 when S3 upload fails, DynamoDB unchanged."""
        client._mock_table.get_item.return_value = sample_app_record
        client._mock_s3.put_object.side_effect = Exception('S3 service error')

        data = {
            'userId': 'user123',
            'file': (io.BytesIO(b'%PDF-1.4 content'), 'resume.pdf', 'application/pdf')
        }

        response = client.post(
            '/api/applications/app456/cv',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 503
        resp_data = response.get_json()
        assert 'error' in resp_data

        # DynamoDB should NOT have been updated
        client._mock_table.update_item.assert_not_called()


class TestCVUploadOverwrite:
    """Tests for overwrite behavior (Requirement 1.6)."""

    def test_reupload_replaces_existing_cv(self, client):
        """Validates: Requirements 1.6 - Re-upload overwrites previous CV in S3 and updates metadata."""
        # Application already has a CV
        client._mock_table.get_item.return_value = {
            'Item': {
                'userId': 'user123',
                'id': 'app456',
                'company': 'Acme Corp',
                'role': 'Engineer',
                'cvS3Key': 'user123/app456/old_resume.pdf',
                'cvFilename': 'old_resume.pdf',
            }
        }
        client._mock_s3.put_object.return_value = {}
        client._mock_table.update_item.return_value = {}

        data = {
            'userId': 'user123',
            'file': (io.BytesIO(b'%PDF-1.4 new content'), 'new_resume.pdf', 'application/pdf')
        }

        response = client.post(
            '/api/applications/app456/cv',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 200
        resp_data = response.get_json()
        assert resp_data['status'] == 'ok'
        assert resp_data['filename'] == 'new_resume.pdf'
        assert resp_data['s3Key'] == 'user123/app456/new_resume.pdf'

        # Verify S3 was called with the new file key
        call_kwargs = client._mock_s3.put_object.call_args[1]
        assert call_kwargs['Key'] == 'user123/app456/new_resume.pdf'

        # Verify DynamoDB was updated with new metadata
        client._mock_table.update_item.assert_called_once_with(
            Key={'userId': 'user123', 'id': 'app456'},
            UpdateExpression='SET cvS3Key = :s3key, cvFilename = :fname',
            ExpressionAttributeValues={
                ':s3key': 'user123/app456/new_resume.pdf',
                ':fname': 'new_resume.pdf'
            }
        )
