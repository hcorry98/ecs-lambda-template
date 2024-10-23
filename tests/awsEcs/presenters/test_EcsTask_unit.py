import io
import os
from contextlib import redirect_stdout
from io import StringIO
from unittest import TestCase
from unittest.mock import patch

import pandas as pd
from environ.compat import ImproperlyConfigured

from awsEcs.presenters.EcsTask import EcsS3Service, EcsTask, NextAppFacade
from common.models.EnvVar import EnvVar
from common.Names import APP_NAME, NEXT_APP_NAME

class TestEcsTaskUnit(TestCase):
    """Unit tests for EcsTask."""

    TEST_FILE_LOC = 'tests/common/testData/'
    TEST_FILE_NAME = 'CompletedHints.csv'
    TEST_ENV = 'stg'
    DATA_BUCKET_NAME = f'{APP_NAME}-data-{TEST_ENV}'
    NEXT_DATA_BUCKET_NAME = f'{NEXT_APP_NAME}-data-{TEST_ENV}'
    testFileKey = "bucket/key"
    csvStringIO = None

    # all setup is done in _instantiateEcsTask, separately in each test, so no setUp function

    @patch('awsEcs.presenters.EcsTask.EcsS3Service')
    @patch('awsEcs.presenters.EcsTask.NextAppFacade')
    def _instantiateEcsTask(self, mockNextAppFacade, mockS3Service):
        """Helper function to instantiate `self.ecsTask` based on the current `self.testFileKey`"""
        # Setup environment
        osEnv = {
            'INFILE': self.testFileKey,
            'ENV': self.TEST_ENV
        } 
        os.environ.update(osEnv)

        self.ecsTask = EcsTask()
        self.ecsTask.nextAppFacade = mockNextAppFacade.return_value

        self.csvStringIO = self._getTestCSVData()
        mockS3Service.return_value.readFile.return_value = self.csvStringIO
        self.ecsTask.s3 = mockS3Service.return_value

    def tearDown(self):
        """Tear down for each test."""
        # Clear environment
        EnvVar.delete()
        os.environ.pop('INFILE', None)
        os.environ.pop('ENV', None)
        if self.csvStringIO:
            self.csvStringIO.seek(0)

    def _getTestCSVData(self):
        """Helper function to get the test CSV data."""
        csvStringIO = io.StringIO()
        filename = f'{self.TEST_FILE_LOC}{self.TEST_FILE_NAME}'
        pd.read_csv(filename).to_csv(csvStringIO, index=False)
        csvStringIO.seek(0)
        return csvStringIO

    # Constructor tests
    def test_constructor(self):
        """Tests if EcsTask can be successfully initialized."""
        self._instantiateEcsTask()

        ecsTask = EcsTask()
        # has INFILE_KEY
        self.assertEqual(ecsTask.INFILE_KEY, self.testFileKey)
        # has INFILE_NAME
        self.assertEqual(ecsTask.INFILE_NAME, self.testFileKey.split('/')[-1])
        # has s3
        self.assertTrue(isinstance(ecsTask.s3, EcsS3Service))
        # # has env, and it is applied correctly
        self.assertEqual(ecsTask.s3.dataBucketName, self.DATA_BUCKET_NAME)
        self.assertEqual(ecsTask.s3.nextAppDataBucketName, self.NEXT_DATA_BUCKET_NAME)
        # env is lowercase
        self.assertEqual(ecsTask.s3.dataBucketName, ecsTask.s3.dataBucketName.lower())
        self.assertEqual(ecsTask.s3.nextAppDataBucketName, ecsTask.s3.nextAppDataBucketName.lower())

        self.assertTrue(isinstance(ecsTask.nextAppFacade, NextAppFacade))

    def test_constructor_SingleSegmentInfileKey(self):
        """Tests if EcsTask can be successfully initialized with a single segment infile key."""
        store_test_file_key = self.testFileKey
        self.testFileKey = "thisIsAllOneWord"
        self._instantiateEcsTask()

        ecsTask = EcsTask()
        # has INFILE_KEY
        self.assertEqual(ecsTask.INFILE_KEY, self.testFileKey)
        # has INFILE_NAME
        self.assertEqual(ecsTask.INFILE_NAME, self.testFileKey.split('/')[-1])
        # has s3
        self.assertTrue(isinstance(ecsTask.s3, EcsS3Service))
        # # has env, and it is applied correctly
        self.assertEqual(ecsTask.s3.dataBucketName, self.DATA_BUCKET_NAME)
        self.assertEqual(ecsTask.s3.nextAppDataBucketName, self.NEXT_DATA_BUCKET_NAME)
        # env is lowercase
        self.assertEqual(ecsTask.s3.dataBucketName, ecsTask.s3.dataBucketName.lower())
        self.assertEqual(ecsTask.s3.nextAppDataBucketName, ecsTask.s3.nextAppDataBucketName.lower())

        self.assertTrue(isinstance(ecsTask.nextAppFacade, NextAppFacade))

        self.testFileKey = store_test_file_key

    def test_constructor_EmptyInfileKey(self):
        """Tests if EcsTask can be successfully initialized with an empty infile."""
        store_test_file_key = self.testFileKey
        self.testFileKey = ""
        self._instantiateEcsTask()

        ecsTask = EcsTask()
        # has INFILE_KEY
        self.assertEqual(self.ecsTask.INFILE_KEY, self.testFileKey)
        # has INFILE_NAME
        self.assertEqual(self.ecsTask.INFILE_NAME, self.testFileKey.split('/')[-1])
        # has s3
        self.assertTrue(isinstance(ecsTask.s3, EcsS3Service))
        # has env, and it is applied correctly
        self.assertEqual(ecsTask.s3.dataBucketName, self.DATA_BUCKET_NAME)
        self.assertEqual(ecsTask.s3.nextAppDataBucketName, self.NEXT_DATA_BUCKET_NAME)
        # env is lowercase
        self.assertEqual(ecsTask.s3.dataBucketName, ecsTask.s3.dataBucketName.lower())
        self.assertEqual(ecsTask.s3.nextAppDataBucketName, ecsTask.s3.nextAppDataBucketName.lower())

        self.assertTrue(isinstance(ecsTask.nextAppFacade, NextAppFacade))

        self.testFileKey = store_test_file_key

    def test_constructor_noEnv(self):
        """Tests if EcsTask raises a KeyError when initialized without an environment."""
        # create instance of envVar but remove 'ENV' key
        envVar = EnvVar()
        del os.environ['ENV']

        with self.assertRaises((KeyError, ImproperlyConfigured)):
            EcsTask()
        osEnv = {
            'INFILE': self.testFileKey,
            'ENV': self.TEST_ENV
        } 
        os.environ.update(osEnv)

    def test_constructor_noInfile(self):
        """Tests if EcsTask raises a KeyError when initialized without an infile."""
        # create instance of envVar but remove 'INFILE' key
        envVar = EnvVar()
        del os.environ['INFILE']

        with self.assertRaises((KeyError, ImproperlyConfigured)):
            EcsTask()
        osEnv = {
            'INFILE': self.testFileKey,
            'ENV': self.TEST_ENV
        } 
        os.environ.update(osEnv)

    # Run tests
    def test_run(self):
        """Tests if EcsTask can be successfully run."""
        self._instantiateEcsTask()

        with redirect_stdout(None):
            self.ecsTask.run()

        self.csvStringIO.seek(0) # reset CSV input

        self.ecsTask.s3.readFile.assert_called_once_with(self.ecsTask.INFILE_KEY)
        self.assertEqual(
                self.ecsTask.s3.writeOutputFile.call_args.args[0].getvalue(),
                StringIO(pd.read_csv(self.csvStringIO).to_csv()).getvalue()
            )
        self.assertEqual(
                self.ecsTask.s3.writeOutputFile.call_args.args[1],
                self.ecsTask.INFILE_NAME
            )
        self.ecsTask.s3.moveFile.assert_called_once_with(self.ecsTask.INFILE_KEY, f'Done/{self.ecsTask.INFILE_NAME}')
        self.ecsTask.nextAppFacade.run.assert_called_once_with(f'ToDo/{self.ecsTask.INFILE_NAME}')

    def test_run_SingleSegmentInfileKey(self):
        """Tests if EcsTask can be successfully run with a single segment infile key."""
        store_test_file_key = self.testFileKey
        self.testFileKey = "thisIsAllOneWord"
        self._instantiateEcsTask()

        with redirect_stdout(None):
            self.ecsTask.run()
        
        self.csvStringIO.seek(0) # reset CSV input

        self.ecsTask.s3.readFile.assert_called_once_with(self.ecsTask.INFILE_KEY)
        self.assertEqual(
                self.ecsTask.s3.writeOutputFile.call_args.args[0].getvalue(),
                StringIO(pd.read_csv(self.csvStringIO).to_csv()).getvalue()
            )
        self.assertEqual(
                self.ecsTask.s3.writeOutputFile.call_args.args[1],
                self.ecsTask.INFILE_NAME
            )
        self.ecsTask.s3.moveFile.assert_called_once_with(self.ecsTask.INFILE_KEY, f'Done/{self.ecsTask.INFILE_NAME}')
        self.ecsTask.nextAppFacade.run.assert_called_once_with(f'ToDo/{self.ecsTask.INFILE_NAME}')

        self.testFileKey = store_test_file_key

    def test_run_EmptyInfileKey(self):
        """Tests if EcsTask can be successfully run with an empty infile."""
        store_test_file_key = self.testFileKey
        self.testFileKey = ""
        self._instantiateEcsTask()

        with redirect_stdout(None):
            self.ecsTask.run()
                
        self.csvStringIO.seek(0) # reset CSV input

        self.ecsTask.s3.readFile.assert_called_once_with(self.ecsTask.INFILE_KEY)
        self.assertEqual(
                self.ecsTask.s3.writeOutputFile.call_args.args[0].getvalue(),
                StringIO(pd.read_csv(self.csvStringIO).to_csv()).getvalue()
            )
        self.assertEqual(
                self.ecsTask.s3.writeOutputFile.call_args.args[1],
                self.ecsTask.INFILE_NAME
            )
        self.ecsTask.s3.moveFile.assert_called_once_with(self.ecsTask.INFILE_KEY, f'Done/{self.ecsTask.INFILE_NAME}')
        self.ecsTask.nextAppFacade.run.assert_called_once_with(f'ToDo/{self.ecsTask.INFILE_NAME}')

        self.testFileKey = store_test_file_key

    def test_run_EmptyInfile(self):
        """Tests that EcsTask errors out if run with an empty infile."""
        self._instantiateEcsTask()
        self.ecsTask.s3.readFile.return_value = StringIO()

        with redirect_stdout(None):
            with self.assertRaises(pd.errors.EmptyDataError):
                self.ecsTask.run()
