import io
import os
from contextlib import redirect_stdout
from io import StringIO
from unittest import TestCase
from unittest.mock import Mock, patch

import pandas as pd
from environ.compat import ImproperlyConfigured

from awsEcs.models.services.EcsS3Service import EcsS3Service
from awsEcs.models.services.NextAppFacade import NextAppFacade
from awsEcs.presenters.EcsTask import EcsTask
from common.models.EnvVar import EnvVar

class TestEcsTaskUnit(TestCase):
    """Unit tests for EcsTask."""

    TEST_FILE_LOC = 'tests/common/testData/'
    TEST_FILE_NAME = 'CompletedHints.csv'
    TEST_ENV = EnvVar()['ENV']
    testFileKey = "bucket/key"
    csvStringIO = None

    # all setup is done in _instantiateEcsTask, separately in each test, so no setUp function

    def _instantiateEcsTask(self):
        """Helper function to instantiate `self.ecsTask` based on the current `self.testFileKey`"""
        # Setup environment
        osEnv = {
            'INFILE': self.testFileKey,
            'ENV': self.TEST_ENV
        } 
        os.environ.update(osEnv)

        self.csvStringIO = self._getTestCSVData()

        patcher = patch('awsEcs.presenters.EcsTask.EcsS3Service')
        self.addCleanup(patcher.stop)
        mockS3Service = patcher.start()

        patcher = patch('awsEcs.presenters.EcsTask.NextAppFacade')
        self.addCleanup(patcher.stop)
        mockNextAppFacade = patcher.start()

        self.mockS3ServiceInstance = Mock(spec=EcsS3Service)
        self.mockS3ServiceInstance.readFile.return_value = self.csvStringIO
        mockS3Service.return_value = self.mockS3ServiceInstance

        self.ecsTask = EcsTask(test=True)

        self.csvStringIO.seek(0) # reset CSV input

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
    def test_constructor_noEnv(self):
        """Tests if EcsTask raises a KeyError when initialized without an environment."""
        # create instance of envVar but remove 'ENV' key
        envVar = EnvVar()
        del os.environ['ENV']

        with self.assertRaises((KeyError, ImproperlyConfigured)):
            EcsTask(test=True)
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
            EcsTask(test=True)
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
                StringIO(pd.read_csv(self.csvStringIO).to_csv(index=False)).getvalue()
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
                StringIO(pd.read_csv(self.csvStringIO).to_csv(index=False)).getvalue()
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
                StringIO(pd.read_csv(self.csvStringIO).to_csv(index=False)).getvalue()
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
        self.mockS3ServiceInstance.readFile.return_value = StringIO()

        with redirect_stdout(None):
            with self.assertRaises(pd.errors.EmptyDataError):
                self.ecsTask.run()
