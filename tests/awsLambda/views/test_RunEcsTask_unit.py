import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from awsLambda.presenters.Validator import Validator
from awsLambda.views.RunEcsTask import RunEcsTask
from common.models.EnvVar import EnvVar
from common.Names import SUBDOMAIN

class TestRunEcsTaskUnit(unittest.TestCase):
    """Unit tests the Lambda RunEcsTask view class."""

    @patch('awsLambda.presenters.Validator.Validator.validate')
    def setUp(self, mockValidate):
        """Set up the RunEcsTask instance for testing."""
        mockValidate.return_value = (200, {'message': 'Request comes from a valid source.'})
        validator = Validator()
        validator.validate = mockValidate
        mockEvent = {
            'httpMethod': 'GET',
            'headers': {'origin': f'https://{SUBDOMAIN}.rll.byu.edu'},
            'body': ''
        }
        self.runEcsTask = RunEcsTask(mockEvent, validator)

        self.expectedResponse = {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': f'https://{SUBDOMAIN}.rll.byu.edu'},
            'body': '{"message": "Ran successfully."}'
        }

        self.TEST_ENV = 'prd'
        osEnv = {
            'ENV': self.TEST_ENV
        } 
        os.environ.update(osEnv)

    def tearDown(self):
        """Remove the test environment variable after each test."""
        del os.environ['ENV']

    @patch('awsLambda.presenters.EcsPresenter.EcsPresenter.run')
    def test_handle(self, mockRun):
        """Ensure the handle method calls the correct methods and returns the correct response."""
        mockRun.return_value = (200, {'message': 'Ran successfully.'})

        with redirect_stdout(None):
            response = self.runEcsTask.handle()

        self.assertEqual(response, self.expectedResponse)
        mockRun.assert_called_once()

        EnvVar.delete()

    @patch('awsLambda.views.Handle.Handle._run')
    @patch('awsLambda.presenters.Validator.Validator.validate')
    def test_handle_failValidation(self, mockValidate, mockRun):
        """Ensure the handle method returns the correct response when validation fails."""
        self.expectedResponse['statusCode'] = 403
        self.expectedResponse['body'] = '{"error": "Request does not come from an allowed domain."}'

        mockValidate.return_value = (403, {'error': 'Request does not come from an allowed domain.'})
        self.runEcsTask.validator.validate = mockValidate

        with redirect_stdout(None):
            response = self.runEcsTask.handle()
        
        self.assertEqual(response, self.expectedResponse)
        mockRun.assert_not_called()

    def test_handle_uncaughtException(self):
        """Ensure the handle method returns the correct response when an uncaught exception occurs."""
        self.expectedResponse['statusCode'] = 500
        self.expectedResponse['body'] = '{"error": "Internal Server Error"}'

        with redirect_stdout(None):
            response = self.runEcsTask.handle()

        self.assertEqual(response, self.expectedResponse)

    @patch('awsLambda.presenters.EcsPresenter.EcsPresenter.run')
    def test_run(self, mockRun):
        """Ensure the _run method calls the correct methods and returns the correct response."""
        mockRun.assert_not_called()
        mockRun.return_value = (200, {'message': 'Ran successfully.'})

        statusCode, response = self.runEcsTask._run()

        self.assertEqual(statusCode, 200)
        self.assertEqual(response, {'message': 'Ran successfully.'})
        mockRun.assert_called_once()

        EnvVar.delete()
