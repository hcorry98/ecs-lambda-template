import json
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

import boto3

from awsLambda.views.main import handle_runEcsTask
from common.models.EnvVar import EnvVar
from common.Names import APP_NAME, SUBDOMAIN

# TODO: Remove the following line when ready to run integration tests
raise unittest.SkipTest("Skipping awsLambda/main integration tests")

class TestLambdaIntegration(unittest.TestCase):
    """Integration tests for Lambda."""

    TEST_FILE_LOC = 'tests/common/testData/'
    TEST_FILE_NAME = 'CompletedHints.csv'
    TEST_ENV = EnvVar()['ENV']
    DATA_BUCKET_NAME = f'{APP_NAME}-data-{TEST_ENV}'

    def setUp(self):
        """Set up for each test which uploads a test file to the data bucket."""
        # Add test file to data bucket
        AWS_REGION = 'us-west-2'
        session = boto3.Session(region_name=AWS_REGION)
        self.client = session.client('s3')

        self.testFileKey = f'ToDo/{self.TEST_FILE_NAME}'
        self.client.upload_file(
            Filename=f'{self.TEST_FILE_LOC}{self.TEST_FILE_NAME}', 
            Bucket=self.DATA_BUCKET_NAME, 
            Key=self.testFileKey
        )

        mockClient = Mock()
        mockClient.return_value.list_task_definitions.return_value = {'taskDefinitionArns': ['fakeArn']}
        mockClient.return_value.describe_security_groups.return_value = {'SecurityGroups': [{'GroupId': 'fakeGroupId'}]}

        self.patcher = patch('boto3.client', mockClient)
        self.patcher.start()

        patcher = patch('awsLambda.presenters.EcsPresenter.BugReporter')
        self.addCleanup(patcher.stop)
        self.mockBugReporter = patcher.start()

        origin = f'https://{SUBDOMAIN}.{"rll" if self.TEST_ENV == "prd" else "rll-dev"}.byu.edu'
        self.mockEvent = {
            'headers': {'origin': origin},
            'body': json.dumps({'inputFile': self.testFileKey})
        }

        # Setup environment
        osEnv = {
            'INFILE': self.testFileKey,
            'ENV': self.TEST_ENV
        } 
        os.environ.update(osEnv)

    def tearDown(self):
        """Tear down for each test which removes the test file from the data bucket."""
        self.patcher.stop()

        # Remove test file from data bucket
        self.client.delete_object(Bucket=self.DATA_BUCKET_NAME, Key=self.testFileKey)

        # Delete moved file from data bucket
        movedFileKey = f'InProgress/{self.TEST_FILE_NAME}'
        self.client.delete_object(Bucket=self.DATA_BUCKET_NAME, Key=movedFileKey)
        
        # Clear environment
        EnvVar.delete()
        del os.environ['INFILE']
        del os.environ['ENV']

    def test_success(self):
        """Tests if Lambda successfully runs on a file."""
        # Verify that the file is only in the ToDo folder
        todoResponse = self.client.list_objects_v2(Bucket=self.DATA_BUCKET_NAME, Prefix='ToDo/')
        inProgressResponse = self.client.list_objects_v2(Bucket=self.DATA_BUCKET_NAME, Prefix='InProgress/')

        todoResponse['Contents'].sort(key=lambda x: x['LastModified'], reverse=True)
        self.assertEqual(todoResponse['Contents'][0]['Key'], f'ToDo/{self.TEST_FILE_NAME}')

        if 'Contents' in inProgressResponse:
            inProgressResponse['Contents'].sort(key=lambda x: x['LastModified'], reverse=True)
            self.assertNotEqual(inProgressResponse['Contents'][0]['Key'], f'InProgress/{self.TEST_FILE_NAME}')

        with redirect_stdout(None):
            response = handle_runEcsTask(self.mockEvent, None)
        self.assertEqual(response['statusCode'], 200)

        # Verify that the file is now in the InProgress folder
        todoResponse = self.client.list_objects_v2(Bucket=self.DATA_BUCKET_NAME, Prefix='ToDo/')
        inProgressResponse = self.client.list_objects_v2(Bucket=self.DATA_BUCKET_NAME, Prefix='InProgress/')

        if 'Contents' in todoResponse:
            todoResponse['Contents'].sort(key=lambda x: x['LastModified'], reverse=True)
            self.assertNotEqual(todoResponse['Contents'][0]['Key'], f'ToDo/{self.TEST_FILE_NAME}')

        inProgressResponse['Contents'].sort(key=lambda x: x['LastModified'], reverse=True)
        self.assertEqual(inProgressResponse['Contents'][0]['Key'], f'InProgress/{self.TEST_FILE_NAME}')

    def test_noFileInS3(self):
        """Tests if Lambda correctly handles nonexistent file."""
        nonexistentFileKey = 'nonexistentFileKey'
        self.mockEvent['body'] = json.dumps({'inputFile': nonexistentFileKey})
        with redirect_stdout(None):
            response = handle_runEcsTask(self.mockEvent, None)
        self.assertEqual(response['statusCode'], 404)

    def test_noInputFileReqBody(self):
        """Tests if Lambda correctly handles no input file key in the request body."""
        self.mockEvent['body'] = json.dumps({})
        with redirect_stdout(None):
            response = handle_runEcsTask(self.mockEvent, None)
        self.assertEqual(response['statusCode'], 400)

    def test_noEnv(self):
        """Tests if Lambda correctly handles no environment variable."""
        # if envVar singleton instance does not exist before the call, environment will refresh
        envVar = EnvVar()
        del os.environ['ENV']
        with redirect_stdout(None):
            response = handle_runEcsTask(self.mockEvent, None)
        self.assertEqual(response['statusCode'], 500)

        # Rebuild environment for tear down
        osEnv = {
            'INFILE': self.testFileKey,
            'ENV': self.TEST_ENV
        } 
        os.environ.update(osEnv)
    
    def test_invalidOrigin(self):
        """Tests if Lambda correctly handles invalid origin."""
        self.mockEvent['headers']['origin'] = 'https://invalid.origin'
        with redirect_stdout(None):
            response = handle_runEcsTask(self.mockEvent, None)
        self.assertEqual(response['statusCode'], 403)
