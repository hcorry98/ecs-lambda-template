import unittest
from unittest.mock import Mock, patch

from awsEcs.models.services.EcsS3Dao import EcsS3Dao

class TestEcsS3DaoUnit(unittest.TestCase):
    """Unit tests for EcsS3Dao."""

    def setUp(self):
        """Sets up the test case."""
        patcher1 = patch('common.models.services.S3Dao.AwsSession')
        self.addCleanup(patcher1.stop)
        mockAwsSession = patcher1.start()
        mockAwsSessionInstance = Mock()
        mockAwsSession.return_value = mockAwsSessionInstance

        self.mockClient = Mock()
        config = {
            'getSession.return_value.client.return_value': self.mockClient
        }
        mockAwsSessionInstance.configure_mock(**config)

        patcher2 = patch('boto3.resource')
        self.addCleanup(patcher2.stop)
        patcher2.start()

        self.ecsS3Dao = EcsS3Dao()

    def test_readFile(self):
        """Tests if readFile returns the correct file contents."""
        # Arrange
        bucket = 'test-bucket'
        key = 'test-key'
        body = 'test-data'
        expected = {'Body': body}

        self.mockClient.get_object.return_value = {
            'Body': body
        }

        # Act
        actual = self.ecsS3Dao.readFile(bucket, key)

        # Assert
        self.assertEqual(actual, expected)

    def test_writeFile(self):
        """Tests if writeFile calls put_object with the correct parameters."""
        # Arrange
        bucket = 'test-bucket'
        key = 'test-key'
        data = 'test-data'
        data = bytes(data, 'utf-8')

        # Act
        self.ecsS3Dao.writeFile(bucket, key, data)

        # Assert
        self.mockClient.put_object.assert_called_once_with(Bucket=bucket, Key=key, Body=data)

# writeFile has no failure states that aren't also AWS failure states
