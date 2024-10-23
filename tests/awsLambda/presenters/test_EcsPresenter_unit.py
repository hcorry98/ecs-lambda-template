from contextlib import redirect_stdout
from unittest import TestCase
from unittest.mock import patch

from botocore.exceptions import ClientError

from awsLambda.presenters.EcsPresenter import EcsPresenter

class TestEcsPresenterUnit(TestCase):
    """Unit tests the Lambda EcsPresenter class."""

    @patch('awsLambda.presenters.EcsPresenter.S3Service')
    @patch('boto3.client')
    @patch('boto3.client')
    def setUp(self, mockEc2Client, mockEcsClient, mockS3Service):
        """Set up the EcsPresenter instance for testing."""
        self.key = 'key'
        event = {'body': '{\"inputFile\": \"key\"}'}
        self.ecsPresenter = EcsPresenter(event)

        self.ecsPresenter.ecsClient = mockEcsClient
        self.ecsPresenter.ecsClient.list_task_definitions.return_value={'taskDefinitionArns': ['1', '2', '3']}
        self.ecsPresenter.ec2Client = mockEc2Client
        self.ecsPresenter.ec2Client.describe_security_groups.return_value={'SecurityGroups': [{'GroupId': '123'}]}
        self.ecsPresenter.s3 = mockS3Service

    def test_run(self):
        """Tests if the run method calls the correct client methods and returns correct values."""
        expectedResponse = {'message': f'Successfully started a task with the key: InProgress/{self.key}'}
        
        self.ecsPresenter.ecsClient.list_task_definitions.assert_not_called()
        self.ecsPresenter.ec2Client.describe_security_groups.assert_not_called()
        self.ecsPresenter.ecsClient.run_task.assert_not_called()
        
        statusCode, response = self.ecsPresenter.run()
        self.assertEqual(200, statusCode)
        self.assertEqual(expectedResponse, response)

        self.ecsPresenter.ecsClient.list_task_definitions.assert_called_once()
        self.ecsPresenter.ec2Client.describe_security_groups.assert_called_once()
        self.ecsPresenter.ecsClient.run_task.assert_called_once()
    
    def test_run_KeyError(self):
        """Tests if run method correctly handles KeyError."""
        expectedResponse = {'error': 'No infile key provided in request body.'}

        self.ecsPresenter.ecsClient.run_task.side_effect = KeyError()
        with redirect_stdout(None):
            statusCode, response = self.ecsPresenter.run()
        self.assertEqual(400, statusCode)
        self.assertEqual(expectedResponse, response)
    
    def test_run_FileNotFoundError(self):
        """Tests if run method correctly handles FileNotFoundError without existing file."""
        expectedResponse = {'error': f'No file found for given infile key: {self.key}'}

        error_response = {'Error': {'Code': 'InvalidArgument'}}
        operation_name = 'test-operation-name'
        self.ecsPresenter.ecsClient.run_task.side_effect = FileNotFoundError(error_response, operation_name)

        with redirect_stdout(None):
            statusCode, response = self.ecsPresenter.run()
        self.assertEqual(404, statusCode)
        self.assertEqual(expectedResponse, response)

    def test_run_ClientError(self):
        """Tests if run method correctly handles ClientError with existing file."""
        expectedResponse = {'error': 'Internal Server Error'}

        self.ecsPresenter.ecsClient.run_task.side_effect = ClientError

        with redirect_stdout(None):
            statusCode, response = self.ecsPresenter.run()
        self.assertEqual(500, statusCode)
        self.assertEqual(expectedResponse, response)

    def test_run_OtherErrors(self):
        """Tests if run method correctly handles other kinds of Exceptions."""
        expectedResponse = {'error': 'Internal Server Error'}

        self.ecsPresenter.ecsClient.run_task.side_effect = RuntimeError

        with redirect_stdout(None):
            statusCode, response = self.ecsPresenter.run()
        self.assertEqual(500, statusCode)
        self.assertEqual(expectedResponse, response)
