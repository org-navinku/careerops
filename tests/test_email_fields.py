"""Unit tests for email field persistence and retrieval."""
import sys
import json
from unittest.mock import MagicMock, patch
from datetime import datetime

sys.path.insert(0, '/Users/navinkumar/workrepos/pers-prj/careerops')

import pytest


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB table for testing."""
    table = MagicMock()
    items = {}

    def put_item_impl(Item=None):
        key = (Item['userId'], Item['id'])
        items[key] = Item

    def get_item_impl(Key=None):
        key = (Key['userId'], Key['id'])
        if key in items:
            return {'Item': items[key]}
        return {}

    def query_impl(KeyConditionExpression=None):
        # Extract userId from KeyConditionExpression (simplified mock)
        user_items = [item for (user_id, _), item in items.items()]
        return {'Items': user_items}

    table.put_item = put_item_impl
    table.get_item = get_item_impl
    table.query = query_impl
    return table, items


@pytest.fixture
def app(mock_dynamodb):
    """Create Flask app with mocked DynamoDB."""
    mock_table, _ = mock_dynamodb

    with patch('backend.applications_table', mock_table):
        from backend import app as flask_app
        flask_app.config['TESTING'] = True
        return flask_app


def test_post_with_email_fields(app, mock_dynamodb):
    """Test that POST with emailSubject and emailTo stores them correctly."""
    mock_table, items = mock_dynamodb

    with patch('backend.applications_table', mock_table):
        with app.test_client() as client:
            payload = {
                'userId': 'user123',
                'id': 'app001',
                'company': 'ACME Corp',
                'role': 'Engineer',
                'dateApplied': '2024-01-15',
                'emailSubject': 'Application for Senior Engineer Role',
                'emailTo': 'hiring@acme.com'
            }

            response = client.post('/api/applications',
                                   json=payload,
                                   content_type='application/json')

            assert response.status_code == 200
            key = ('user123', 'app001')
            assert key in items
            stored_item = items[key]
            assert stored_item['emailSubject'] == 'Application for Senior Engineer Role'
            assert stored_item['emailTo'] == 'hiring@acme.com'


def test_post_without_email_fields_defaults_to_empty(app, mock_dynamodb):
    """Test that POST without emailSubject and emailTo defaults them to empty string."""
    mock_table, items = mock_dynamodb

    with patch('backend.applications_table', mock_table):
        with app.test_client() as client:
            payload = {
                'userId': 'user123',
                'id': 'app002',
                'company': 'TechCorp',
                'role': 'Designer'
            }

            response = client.post('/api/applications',
                                   json=payload,
                                   content_type='application/json')

            assert response.status_code == 200
            key = ('user123', 'app002')
            assert key in items
            stored_item = items[key]
            assert stored_item['emailSubject'] == ''
            assert stored_item['emailTo'] == ''


def test_put_updates_email_fields(app, mock_dynamodb):
    """Test that PUT updates emailSubject and emailTo via the merge logic."""
    mock_table, items = mock_dynamodb

    with patch('backend.applications_table', mock_table):
        with app.test_client() as client:
            initial_payload = {
                'userId': 'user123',
                'id': 'app003',
                'company': 'StartupXYZ',
                'role': 'PM',
                'emailSubject': 'Initial Subject',
                'emailTo': 'initial@startup.com'
            }

            client.post('/api/applications',
                       json=initial_payload,
                       content_type='application/json')

            update_payload = {
                'userId': 'user123',
                'emailSubject': 'Updated Subject Line',
                'emailTo': 'updated@startup.com'
            }

            response = client.put('/api/applications/app003',
                                 json=update_payload,
                                 content_type='application/json')

            assert response.status_code == 200
            key = ('user123', 'app003')
            updated_item = items[key]
            assert updated_item['emailSubject'] == 'Updated Subject Line'
            assert updated_item['emailTo'] == 'updated@startup.com'


def test_get_returns_email_fields(app, mock_dynamodb):
    """Test that GET returns both emailSubject and emailTo in the response."""
    mock_table, items = mock_dynamodb

    with patch('backend.applications_table', mock_table):
        with app.test_client() as client:
            payload = {
                'userId': 'user123',
                'id': 'app004',
                'company': 'TechCorp',
                'role': 'Engineer',
                'emailSubject': 'Test Subject',
                'emailTo': 'test@techcorp.com'
            }

            client.post('/api/applications',
                       json=payload,
                       content_type='application/json')

            response = client.get('/api/applications?userId=user123')
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) >= 1
            app_item = data[0]
            assert app_item['emailSubject'] == 'Test Subject'
            assert app_item['emailTo'] == 'test@techcorp.com'
