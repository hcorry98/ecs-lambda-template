import os
import unittest
from contextlib import redirect_stdout
from unittest import TestCase
from unittest.mock import patch

import boto3
from botocore.exceptions import ClientError
from environ.compat import ImproperlyConfigured

from awsEcs.presenters.EcsTask import EcsTask
from common.models.EnvVar import EnvVar
from common.Names import APP_NAME, NEXT_APP_NAME

# TODO: Remove the following line when ready to run integration tests
raise unittest.SkipTest("Skipping awsEcs/EcsTask integration tests")

class TestEcsTaskIntegration(TestCase):
    """Integration tests for EcsTask."""

    TEST_FILE_LOC = 'tests/common/testData/'
    TEST_FILE_NAME = 'CompletedHints.csv'
    INVALID_FILE_NAME = 'Invalid.txt'
    TEST_ENV = EnvVar()['ENV']
    DATA_BUCKET_NAME = f'{APP_NAME}-data-{TEST_ENV}'
    NEXT_DATA_BUCKET_NAME = f'{NEXT_APP_NAME}-data-{TEST_ENV}'

    def setUp(self):
        """Set up for each test."""
        # Add test file to data bucket
        AWS_REGION = 'us-west-2'
        session = boto3.Session(region_name=AWS_REGION)
        self.client = session.client('s3')
        self.testFileKey = f'InProgress/{self.TEST_FILE_NAME}'
    
    def _uploadTestFile(self):
        """Uploads a test file to the data bucket and sets up the environment."""
        self.client.upload_file(
            Filename=f'{self.TEST_FILE_LOC}{self.TEST_FILE_NAME}', 
            Bucket=self.DATA_BUCKET_NAME, 
            Key=self.testFileKey
        )

        # Setup environment
        osEnv = {
            'INFILE': self.testFileKey,
            'ENV': self.TEST_ENV
        } 
        os.environ.update(osEnv)

    def tearDown(self):
        """Tear down for each test which removes the test file from the data bucket."""
        # Remove test file from data bucket
        self.client.delete_object(Bucket=self.DATA_BUCKET_NAME, Key=self.testFileKey)

    def _deleteTestFile(self):
        """Deletes the test file from the data bucket and clears the environment."""
        # Delete output file from data bucket and from SerializerGS's data bucket
        outFileKey = f'Output/{self.TEST_FILE_NAME}'
        self.client.delete_object(Bucket=self.DATA_BUCKET_NAME, Key=outFileKey)
        nextAppOutKey = f'ToDo/{self.TEST_FILE_NAME}'
        self.client.delete_object(Bucket=self.NEXT_DATA_BUCKET_NAME, Key=nextAppOutKey)
        
        # Clear environment - have to use pop instead of del to avoid a KeyError when called twice for nonCsvFile
        EnvVar.delete() 
        os.environ.pop('INFILE', None)
        os.environ.pop('ENV', None)

    @patch('awsEcs.presenters.EcsTask.NextAppFacade')
    def test_success(self, mockNextAppFacade):
        """Tests if EcsTask successfully runs on a file."""
        self._uploadTestFile()

        with redirect_stdout(None):
            ecsTask = EcsTask(test=True)
            ecsTask.run()
            
        self.testFileKey = f'Done/{self.TEST_FILE_NAME}'

        ecsTaskDoneResponse = self.client.list_objects_v2(Bucket=self.DATA_BUCKET_NAME, Prefix='Done/')
        ecsTaskOutputResponse = self.client.list_objects_v2(Bucket=self.DATA_BUCKET_NAME, Prefix='Output/')
        nextAppResponse = self.client.list_objects_v2(Bucket=self.NEXT_DATA_BUCKET_NAME, Prefix='ToDo/')

        # get most recent item
        ecsTaskDoneResponse['Contents'].sort(key=lambda x: x['LastModified'], reverse=True)
        self.assertEqual(ecsTaskDoneResponse['Contents'][0]['Key'], self.testFileKey)

        ecsTaskOutputResponse['Contents'].sort(key=lambda x: x['LastModified'], reverse=True)
        self.assertEqual(ecsTaskOutputResponse['Contents'][0]['Key'], f'Output/{self.TEST_FILE_NAME}')

        nextAppResponse['Contents'].sort(key=lambda x: x['LastModified'], reverse=True)
        self.assertEqual(nextAppResponse['Contents'][0]['Key'], f'ToDo/{self.TEST_FILE_NAME}')

        mockNextAppFacade.return_value.run.assert_called_once_with(f'ToDo/{self.TEST_FILE_NAME}')

        self._deleteTestFile()

    # constructor failure states
    def test_noEnv(self):
        """Tests if EcsTask raises a KeyError when run without an environment."""
        self._uploadTestFile()
        envVar = EnvVar()
        del os.environ['ENV']
        with redirect_stdout(None):
            with self.assertRaises((KeyError, ImproperlyConfigured)):
                EcsTask(test=True)
        
        osEnv = {
            'INFILE': self.testFileKey,
            'ENV': self.TEST_ENV
        }
        os.environ.update(osEnv)

        self._deleteTestFile()

    def test_invalidEnv(self):
        """Tests if EcsTask raises a NoSuchBucket error when run with an invalid environment."""
        os.environ['ENV'] = 'invalid'
        with redirect_stdout(None):
            ecsTask = EcsTask(test=True)
            with self.assertRaises(Exception) as e:
                ecsTask.run()

        error = e.exception
        self.assertEqual(error.response['Error']['Code'], 'NoSuchBucket')
        self.assertEqual(error.response['Error']['Message'], 'The specified bucket does not exist')
        self.assertEqual(error.response['Error']['BucketName'], f'{APP_NAME}-data-invalid')
        self.assertEqual(error.operation_name, 'GetObject')

    # run method failure states
    def test_nonexistentFile(self):
        """Tests if EcsTask raises a ClientError when run on a file that does not exist."""
        self._uploadTestFile()

        os.environ['INFILE'] = 'no-such-file'
        with redirect_stdout(None):
            ecsTask = EcsTask(test=True)
            with self.assertRaises(ClientError) as e:
                ecsTask.run()

        error = e.exception
        self.assertEqual(error.response['Error']['Code'], 'NoSuchKey')
        self.assertEqual(error.response['Error']['Message'], 'The specified key does not exist.')
        self.assertEqual(error.response['Error']['Key'], 'no-such-file')
        self.assertEqual(error.operation_name, 'GetObject')

        self._deleteTestFile()

    def test_noInFile(self):
        """Tests if EcsTask raises a KeyError when initalized without an input file."""
        self._uploadTestFile()
        envVar = EnvVar()
        del os.environ['INFILE']
        with redirect_stdout(None):
            with self.assertRaises((KeyError, ImproperlyConfigured)):
                EcsTask(test=True)

        osEnv = {
            'INFILE': self.testFileKey,
            'ENV': self.TEST_ENV
        }
        os.environ.update(osEnv)

        self._deleteTestFile()

    @patch('awsEcs.models.services.NextAppFacade.NextAppFacade')
    def test_nonCsvFile(self, mockNextAppFacade):
        """Tests if EcsTask completes execution when pointed at a file that isn't a CSV."""
        # Arrange
        store_test_file_name = self.TEST_FILE_NAME
        self.TEST_FILE_NAME = self.INVALID_FILE_NAME
        self._uploadTestFile()

        # Act
        with redirect_stdout(None):
            ecsTask = EcsTask(test=True)
            ecsTask.nextAppFacade = mockNextAppFacade
            ecsTask.run()

        # one-time cleanup
        self._deleteTestFile()
        self.TEST_FILE_NAME = store_test_file_name
