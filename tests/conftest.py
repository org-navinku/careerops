"""Shared test fixtures - mock boto3 before importing backend."""
import sys
from unittest.mock import MagicMock

# Mock boto3 and botocore in sys.modules before backend is imported
# This is needed because boto3 is not installed in the test venv

mock_boto3 = MagicMock()
mock_botocore = MagicMock()
mock_botocore_exceptions = MagicMock()


class MockClientError(Exception):
    """Mock botocore ClientError."""
    def __init__(self, error_response=None, operation_name='Unknown'):
        self.response = error_response or {'Error': {'Code': 'Unknown', 'Message': 'Unknown'}}
        self.operation_name = operation_name
        super().__init__(str(self.response))


mock_botocore_exceptions.ClientError = MockClientError

# Install mocks into sys.modules before backend.py gets imported
sys.modules['boto3'] = mock_boto3
sys.modules['boto3.dynamodb'] = MagicMock()
sys.modules['boto3.dynamodb.conditions'] = MagicMock()
sys.modules['botocore'] = mock_botocore
sys.modules['botocore.exceptions'] = mock_botocore_exceptions
