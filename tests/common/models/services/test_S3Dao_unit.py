import unittest
from unittest.mock import Mock, patch

from common.models.services.S3Dao import S3Dao

class TestS3DaoUnit(unittest.TestCase):
    """Unit tests for S3Dao."""

    def setUp(self):
        """Sets up the test case."""
        patcher = patch('common.models.services.S3Dao.AwsSession')
        self.addCleanup(patcher.stop)
        mockAwsSession = patcher.start()

        mockAwsSessionInstance = Mock()  # S3Dao receives instance when calling AwsSession()
        mockAwsSession.return_value = mockAwsSessionInstance

        self.mockClient = Mock()
        config = {
            'getSession.return_value.client.return_value': self.mockClient
        }
        mockAwsSessionInstance.configure_mock(**config)

        self.s3Dao = S3Dao()

    def test_moveFile(self):
        """Tests if moveFile calls copy_object and delete_object with the correct parameters."""
        self.mockClient.copy_object.assert_not_called()
        self.mockClient.delete_object.assert_not_called()

        # Arrange
        oldBucket = 'test-bucket'
        oldKey = 'test-key'
        destBucket = 'test-bucket'
        destKey = 'test-key'

        # Act
        self.s3Dao.moveFile(oldBucket, oldKey, destBucket, destKey)

        # Assert
        self.mockClient.copy_object.assert_called_once_with(
            Bucket=destBucket,
            Key=destKey,
            CopySource={
                'Bucket': oldBucket,
                'Key': oldKey
            }
        )
        self.mockClient.delete_object.assert_called_once_with(Bucket=oldBucket, Key=oldKey)

    # moveFile has no failure states that aren't also AWS failure states
