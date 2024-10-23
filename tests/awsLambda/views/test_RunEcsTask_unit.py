import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from awsLambda.presenters.EcsPresenter import EcsPresenter
from awsLambda.presenters.Validator import Validator
from awsLambda.views.RunEcsTask import RunEcsTask
from common.models.EnvVar import EnvVar
from common.Names import SUBDOMAIN

class TestRunEcsTaskUnit(unittest.TestCase):
    """Unit tests the Lambda RunEcsTask view class."""

    def setUp(self):
        """Sets up the test case."""
        patcher = patch('awsLambda.views.RunEcsTask.EcsPresenter')
        self.addCleanup(patcher.stop)
        mockEcsPresenter = patcher.start()

        self.mockValidatorInstance = Mock(spec=Validator)
        self.mockValidatorInstance.validate.return_value = (200, {'message': 'Request comes from a valid source.'})
        self.mockValidatorInstance.sendCorsResponse.return_value = {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': f'https://{SUBDOMAIN}.rll.byu.edu'},
            'body': '{"message": "Ran successfully."}'
        }

        self.mockEcsPresenterInstance = Mock(spec=EcsPresenter)
        self.mockEcsPresenterInstance.run.return_value = (200, {'message': 'Ran successfully.'})
        mockEcsPresenter.return_value = self.mockEcsPresenterInstance

        mockEvent = {
            'httpMethod': 'GET',
            'headers': {'origin': f'https://{SUBDOMAIN}.rll.byu.edu'},
            'body': ''
        }
        self.runEcsTask = RunEcsTask(mockEvent, self.mockValidatorInstance, True)

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
        """Tears down the test case."""
        del os.environ['ENV']

    def test_handle(self):
        """Ensure the handle method calls the correct methods and returns the correct response."""
        with redirect_stdout(None):
            response = self.runEcsTask.handle()

        self.assertEqual(response, self.expectedResponse)
        self.mockValidatorInstance.validate.assert_called_once()
        self.mockEcsPresenterInstance.run.assert_called_once()

        EnvVar.delete()

    def test_handle_failValidation(self):
        """Ensure the handle method returns the correct response when validation fails."""
        self.expectedResponse['statusCode'] = 403
        self.expectedResponse['body'] = '{"error": "Request does not come from an allowed domain."}'

        self.mockValidatorInstance.validate.return_value = (403, {'error': 'Request does not come from an allowed domain.'})
        self.mockValidatorInstance.sendCorsResponse.return_value = {
            'statusCode': 403,
            'headers': {'Access-Control-Allow-Origin': f'https://{SUBDOMAIN}.rll.byu.edu'},
            'body': '{"error": "Request does not come from an allowed domain."}'
        }

        with redirect_stdout(None):
            response = self.runEcsTask.handle()
        
        self.assertEqual(response, self.expectedResponse)
        self.mockEcsPresenterInstance.run.assert_not_called()
        self.mockValidatorInstance.sendCorsResponse.assert_called_once()
        self.mockValidatorInstance.validate.assert_called_once()

    def test_handle_uncaughtException(self):
        """Ensure the handle method returns the correct response when an uncaught exception occurs."""
        self.expectedResponse['statusCode'] = 500
        self.expectedResponse['body'] = '{"error": "Internal Server Error"}'

        self.mockValidatorInstance.validate.side_effect = Exception('An uncaught exception occurred.')
        self.mockValidatorInstance.sendCorsResponse.return_value = {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': f'https://{SUBDOMAIN}.rll.byu.edu'},
            'body': '{"error": "Internal Server Error"}'
        }

        with redirect_stdout(None):
            response = self.runEcsTask.handle()

        self.assertEqual(response, self.expectedResponse)

    def test_run(self):
        """Ensure the _run method calls the correct methods and returns the correct response."""

        with redirect_stdout(None):
            statusCode, response = self.runEcsTask._run()

        self.assertEqual(statusCode, 200)
        self.assertEqual(response, {'message': 'Ran successfully.'})
        self.mockEcsPresenterInstance.run.assert_called_once()

        EnvVar.delete()
