from contextlib import redirect_stdout
from unittest import TestCase
from unittest.mock import patch

from botocore.exceptions import ClientError

from awsLambda.presenters.EcsPresenter import EcsPresenter

class TestEcsPresenterUnit(TestCase):
    """Unit tests the Lambda EcsPresenter class."""

    def setUp(self):
        """Sets up the test case."""
        patcher = patch('awsLambda.presenters.EcsPresenter.S3Service')
        self.addCleanup(patcher.stop)
        mockS3Service = patcher.start()

        patcher = patch('awsLambda.presenters.EcsPresenter.boto3.client')
        self.addCleanup(patcher.stop)
        self.mockBoto3Client = patcher.start()

        patcher = patch('awsLambda.presenters.EcsPresenter.ParameterService')
        self.addCleanup(patcher.stop)
        mockParameterService = patcher.start()

        self.mockBoto3Client.return_value.list_task_definitions.return_value = {'taskDefinitionArns': ['1', '2', '3']}
        self.mockBoto3Client.return_value.describe_security_groups.return_value = {'SecurityGroups': [{'GroupId': '123'}]}

        self.key = 'key'
        event = {'body': '{\"inputFile\": \"key\"}'}
        self.ecsPresenter = EcsPresenter(event, True)

    def test_run(self):
        """Tests if the run method calls the correct client methods and returns correct values."""
        expectedResponse = {'message': f'Successfully started a task with the key: InProgress/{self.key}'}

        statusCode, response = self.ecsPresenter.run()
        self.assertEqual(200, statusCode)
        self.assertEqual(expectedResponse, response)

        self.mockBoto3Client.return_value.list_task_definitions.assert_called_once()
        self.mockBoto3Client.return_value.describe_security_groups.assert_called_once()
        self.mockBoto3Client.return_value.run_task.assert_called_once()
    
    def test_run_KeyError(self):
        """Tests if run method correctly handles KeyError."""
        expectedResponse = {'error': 'No infile key provided in request body.'}

        self.mockBoto3Client.return_value.run_task.side_effect = KeyError()
        with redirect_stdout(None):
            statusCode, response = self.ecsPresenter.run()
        self.assertEqual(400, statusCode)
        self.assertEqual(expectedResponse, response)
    
    def test_run_FileNotFoundError(self):
        """Tests if run method correctly handles FileNotFoundError without existing file."""
        expectedResponse = {'error': f'No file found for given infile key: {self.key}'}

        error_response = {'Error': {'Code': 'InvalidArgument'}}
        operation_name = 'test-operation-name'
        self.mockBoto3Client.return_value.run_task.side_effect = FileNotFoundError(error_response, operation_name)

        with redirect_stdout(None):
            statusCode, response = self.ecsPresenter.run()
        self.assertEqual(404, statusCode)
        self.assertEqual(expectedResponse, response)

    def test_run_ClientError(self):
        """Tests if run method correctly handles ClientError with existing file."""
        expectedResponse = {'error': 'Internal Server Error'}

        self.mockBoto3Client.return_value.run_task.side_effect = ClientError

        with redirect_stdout(None):
            statusCode, response = self.ecsPresenter.run()
        self.assertEqual(500, statusCode)
        self.assertEqual(expectedResponse, response)

    def test_run_OtherErrors(self):
        """Tests if run method correctly handles other kinds of Exceptions."""
        expectedResponse = {'error': 'Internal Server Error'}

        self.mockBoto3Client.return_value.run_task.side_effect = RuntimeError

        with redirect_stdout(None):
            statusCode, response = self.ecsPresenter.run()
        self.assertEqual(500, statusCode)
        self.assertEqual(expectedResponse, response)
