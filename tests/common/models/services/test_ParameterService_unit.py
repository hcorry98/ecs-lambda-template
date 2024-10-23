import unittest
from unittest.mock import Mock, patch

from common.models.services.ParameterService import ParameterService

class TestParameterServiceUnit(unittest.TestCase):
    """Unit tests for S3Dao."""

    def setUp(self):
        """Set up the S3Dao instance for testing."""
        patcher = patch('common.models.services.ParameterService.AwsSession')
        self.addCleanup(patcher.stop)
        mockAwsSession = patcher.start()

        mockAwsSessionInstance = Mock()  # S3Dao receives instance when calling AwsSession()
        mockAwsSession.return_value = mockAwsSessionInstance
        
        self.mockClient = Mock()
        config = {
            'getSession.return_value.client.return_value': self.mockClient
        }
        mockAwsSessionInstance.configure_mock(**config)

        self.parameterService = ParameterService()

    def test_getPyFSCredentials(self):
        """Tests if getPyFSCredentials calls get_parameter with the correct parameters."""
        # Arrange
        self.mockClient.get_parameter.return_value = {
            'Parameter': {
                'Value': '{"username":"DataFinder","password":"fakepass"}'
            }
        }
        expected = {
            'username': 'DataFinder',
            'password': 'fakepass'
        }

        # Act
        actual = self.parameterService.getPyFSCredentials()

        # Assert
        self.assertEqual(actual, expected)

    def test_getGithubCredentials(self):
        """Tests if getGithubCredentials calls get_parameter with the correct parameters."""
        # Arrange
        self.mockClient.get_parameter.return_value = {
            'Parameter': {
                'Value': 'test-value'
            }
        }

        # Act
        actual = self.parameterService.getGithubCredentials()

        # Assert
        self.assertEqual(actual, 'test-value')
