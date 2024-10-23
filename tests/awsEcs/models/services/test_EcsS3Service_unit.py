import unittest
from contextlib import redirect_stdout
from io import BytesIO, StringIO
from unittest.mock import Mock, call, patch

from botocore.response import StreamingBody

from awsEcs.models.services.EcsS3Dao import EcsS3Dao
from awsEcs.models.services.EcsS3Service import EcsS3Service
from common.models.EnvVar import EnvVar

class TestEcsS3ServiceUnit(unittest.TestCase):
    """Unit tests for EcsS3Service."""

    def setUp(self):
        """Sets up the test case."""
        patcher = patch('awsEcs.models.services.EcsS3Service.EcsS3Dao')
        self.addCleanup(patcher.stop)
        mockEcsS3Dao = patcher.start()
        self.mockEcsS3DaoInstance = Mock(spec=EcsS3Dao)
        mockEcsS3Dao.return_value = self.mockEcsS3DaoInstance

        self.ecsS3Service = EcsS3Service()

    def tearDown(self):
        """Tears down the test case."""
        EnvVar.delete()

    def test_readFile(self):
        """Tests if readFile returns the correct file contents."""
        # Arrange
        key = 'test-key'
        expected = 'test-data\ntest-data\n'

        dataToEncode = bytes(expected, 'utf-8')
        self.mockEcsS3DaoInstance.readFile.return_value = {
            'Body': StreamingBody(BytesIO(dataToEncode), len(dataToEncode))
        }

        # Act
        actual = self.ecsS3Service.readFile(key)

        # Assert
        self.assertEqual(actual.getvalue(), expected)

    def test_readFile_Utf16(self):
        """Tests if readFile fails loudly when passed a file encoded as something other than UTF-8."""
        # Arrange
        key = 'test-key'

        dataToEncode = bytes('test-data\ntest-data\n', 'utf-16')
        self.mockEcsS3DaoInstance.readFile.return_value = {
            'Body': StreamingBody(BytesIO(dataToEncode), len(dataToEncode))
        }

        # Act & Assert
        with self.assertRaises(UnicodeDecodeError):
            actual = self.ecsS3Service.readFile(key)

    def test_readFile_EmptyBody(self):
        """Tests if readFile returns correctly if pointed at an empty file."""
        # Arrange
        key = 'test-key'
        expected = ''

        dataToEncode = bytes(expected, 'utf-8')
        self.mockEcsS3DaoInstance.readFile.return_value  = {
            'Body': StreamingBody(BytesIO(dataToEncode), len(dataToEncode))
        }

        # Act
        actual = self.ecsS3Service.readFile(key)

        # Assert
        self.assertEqual(actual.getvalue(), expected)

    def test_writeOutputFile(self):
        """Tests if writeOutputFile calls writeFile with the correct parameters."""
        # Arrange
        data = Mock()
        outData = data.read().encode('utf8')
        fileName = 'test-file'
        outputKey = 'Output/test-file'
        nextProcessKey = 'ToDo/test-file'

        # Act
        with redirect_stdout(None):
            self.ecsS3Service.writeOutputFile(data, fileName)

        # Assert
        self.mockEcsS3DaoInstance.writeFile.assert_has_calls([call(self.ecsS3Service.dataBucketName, outputKey, outData),
                                        call(self.ecsS3Service.nextAppDataBucketName, nextProcessKey, outData)])

    def test_writeOutputFile_EmptyData(self):
        """Tests if writeOutputFile runs without error if empty data is passed in."""
        # Arrange
        data = StringIO()
        outData = data.read().encode('utf8')
        fileName = 'test-file'
        outputKey = 'Output/test-file'
        nextProcessKey = 'ToDo/test-file'

        # Act
        with redirect_stdout(None):
            self.ecsS3Service.writeOutputFile(data, fileName)

        # Assert
        self.mockEcsS3DaoInstance.writeFile.assert_has_calls([call(self.ecsS3Service.dataBucketName, outputKey, outData),
                                        call(self.ecsS3Service.nextAppDataBucketName, nextProcessKey, outData)])

    def test_writeOutputFile_EmptyFileName(self):
        """Tests if writeOutputFile runs without error if empty file name is passed in."""
        # Arrange
        data = Mock()
        outData = data.read().encode('utf8')
        fileName = ''
        outputKey = 'Output/'
        nextProcessKey = 'ToDo/'

        # Act
        with redirect_stdout(None):
            self.ecsS3Service.writeOutputFile(data, fileName)

        # Assert
        self.mockEcsS3DaoInstance.writeFile.assert_has_calls([call(self.ecsS3Service.dataBucketName, outputKey, outData),
                                        call(self.ecsS3Service.nextAppDataBucketName, nextProcessKey, outData)])
