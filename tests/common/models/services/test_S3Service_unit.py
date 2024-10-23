import unittest
from unittest.mock import Mock, patch

from common.models.EnvVar import EnvVar
from common.models.services.S3Dao import S3Dao
from common.models.services.S3Service import S3Service

class TestS3ServiceUnit(unittest.TestCase):
    """Unit tests for S3Service."""

    def setUp(self):
        """Sets up the test case."""
        patcher = patch('common.models.services.S3Service.S3Dao')
        self.addCleanup(patcher.stop)
        mockS3Dao = patcher.start()
        self.mockS3DaoInstance = Mock(spec=S3Dao)
        mockS3Dao.return_value = self.mockS3DaoInstance

        self.s3Service = S3Service()

    def tearDown(self):
        """Tears down the test case."""
        EnvVar.delete()

    def test_moveFile(self):
        """Ensure the moveFile method calls the correct methods with the correct parameters."""
        file = 'fileName.csv'
        oldKey = f'ToDo/{file}'
        newKey = f'InProgress/{file}'

        self.s3Service.moveFile(oldKey, newKey)

        self.mockS3DaoInstance.moveFile.assert_called_once_with(
            self.s3Service.dataBucketName, oldKey, self.s3Service.dataBucketName, newKey
        )
