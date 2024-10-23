import unittest
from unittest.mock import patch
import os

from common.models.services.S3Service import S3Service

class TestS3ServiceUnit(unittest.TestCase):
    """Unit tests for S3Service."""

    @patch('common.models.services.S3Service.S3Dao')
    @patch('common.models.services.S3Service.EnvVar')
    def setUp(self, mockEnvVar, mockS3Dao):
        """Set up the S3Service instance for testing."""
        self.TEST_ENV = 'stg'
        osEnv = {
            'ENV': self.TEST_ENV
        }
        os.environ.update(osEnv)

        self.s3Service = S3Service()
    
    def tearDown(self):
        """Remove the test environment variable after each test."""
        del os.environ['ENV']

    def test_moveFile(self):
        """Ensure the moveFile method calls the correct methods with the correct parameters."""
        self.s3Service.s3Dao.moveFile.assert_not_called()
        file = 'fileName.csv'
        oldKey = f'ToDo/{file}'
        newKey = f'InProgress/{file}'
        self.s3Service.moveFile(oldKey, newKey)
        self.s3Service.s3Dao.moveFile.assert_called_once_with(self.s3Service.dataBucketName, oldKey, self.s3Service.dataBucketName, newKey)
