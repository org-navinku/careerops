"""Root conftest.py - mock boto3/botocore before any module imports them."""
import sys
from unittest.mock import MagicMock


# This must execute at import time (before pytest collects tests)
_mock_boto3 = MagicMock()
_mock_botocore = MagicMock()


class _MockClientError(Exception):
    """Mock botocore ClientError."""
    def __init__(self, error_response=None, operation_name='Unknown'):
        self.response = error_response or {'Error': {'Code': 'Unknown', 'Message': 'Unknown'}}
        self.operation_name = operation_name
        super().__init__(str(self.response))


_mock_botocore_exceptions = MagicMock()
_mock_botocore_exceptions.ClientError = _MockClientError

# Force-install mocks. This runs when conftest.py is first imported by pytest.
sys.modules['boto3'] = _mock_boto3
sys.modules['boto3.dynamodb'] = MagicMock()
sys.modules['boto3.dynamodb.conditions'] = MagicMock()
sys.modules['botocore'] = _mock_botocore
sys.modules['botocore.exceptions'] = _mock_botocore_exceptions
