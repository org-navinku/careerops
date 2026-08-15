"""Property-based tests for email field persistence using Hypothesis."""
import sys
from unittest.mock import MagicMock, patch
from hypothesis import given, strategies as st, settings, HealthCheck

sys.path.insert(0, '/Users/navinkumar/workrepos/pers-prj/careerops')

import pytest


def create_mock_dynamodb():
    """Create a mock DynamoDB table."""
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
        user_items = [item for (user_id, _), item in items.items()]
        return {'Items': user_items}

    table.put_item = put_item_impl
    table.get_item = get_item_impl
    table.query = query_impl
    return table, items


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    email_subject=st.text(min_size=0, max_size=200),
    email_to=st.text(min_size=0, max_size=200)
)
def test_email_fields_persistence_round_trip(email_subject, email_to):
    """Property 1: Email fields persistence round-trip.

    Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3

    For any generated emailSubject and emailTo values:
    - POST an application with those values
    - GET the application
    - Assert retrieved values match the posted values
    """
    mock_table, items = create_mock_dynamodb()

    with patch('backend.applications_table', mock_table):
        from backend import app as flask_app
        flask_app.config['TESTING'] = True

        with flask_app.test_client() as client:
            payload = {
                'userId': 'user_pbt',
                'id': f'app_pbt_{abs(hash((email_subject, email_to)))}',
                'company': 'TestCorp',
                'role': 'TestRole',
                'dateApplied': '2024-01-15',
                'emailSubject': email_subject,
                'emailTo': email_to
            }

            post_response = client.post(
                '/api/applications',
                json=payload,
                content_type='application/json'
            )

            assert post_response.status_code == 200

            key = ('user_pbt', payload['id'])
            assert key in items, f"Expected key {key} in items, but found {list(items.keys())}"
            stored_item = items[key]

            assert stored_item['emailSubject'] == email_subject, \
                f"Expected emailSubject '{email_subject}' but got '{stored_item['emailSubject']}'"
            assert stored_item['emailTo'] == email_to, \
                f"Expected emailTo '{email_to}' but got '{stored_item['emailTo']}'"


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    company=st.text(min_size=1, max_size=50),
    role=st.text(min_size=1, max_size=50)
)
def test_email_fields_default_on_omission(company, role):
    """Property 2: Email fields default to empty string on creation.

    Validates: Requirements 1.1, 2.1

    For any generated application payload that omits emailSubject and emailTo:
    - POST the payload without those fields
    - GET the record
    - Assert both fields equal empty string
    """
    mock_table, items = create_mock_dynamodb()

    with patch('backend.applications_table', mock_table):
        from backend import app as flask_app
        flask_app.config['TESTING'] = True

        with flask_app.test_client() as client:
            payload = {
                'userId': 'user_default',
                'id': f'app_default_{abs(hash((company, role)))}',
                'company': company,
                'role': role,
                'dateApplied': '2024-01-15'
            }

            post_response = client.post(
                '/api/applications',
                json=payload,
                content_type='application/json'
            )

            assert post_response.status_code == 200

            key = ('user_default', payload['id'])
            assert key in items
            stored_item = items[key]

            assert stored_item['emailSubject'] == '', \
                f"Expected emailSubject to default to '', but got '{stored_item['emailSubject']}'"
            assert stored_item['emailTo'] == '', \
                f"Expected emailTo to default to '', but got '{stored_item['emailTo']}'"
