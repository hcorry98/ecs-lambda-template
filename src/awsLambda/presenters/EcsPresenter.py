import json
import sys
import traceback

import boto3
from botocore.exceptions import ClientError
from PyBugReporter.src.BugReporter import BugReporter

from common.models.EnvVar import EnvVar
from common.models.services.ParameterService import ParameterService
from common.models.services.S3Service import S3Service
from common.Names import PROJECT_NAME

class EcsPresenter:
    """A presenter that runs an ECS task with the given key as an environment variable.

    Attributes:
        PRIVATE_SUBNET_A_ID: the ID of the first private subnet in the VPC
        PRIVATE_SUBNET_B_ID: the ID of the second private subnet in the VPC
        VPC_ID: the ID of the VPC
        ecsClient (boto3.client): the ECS client object
        ec2Client (boto3.client): the EC2 client object
        securityGroupName (str): the security group name for the cluster
        s3 (S3Service): the S3 service object
        event (dict): the event from the API Gateway request to Lambda
    """
     
    def __init__(self, event: dict, test: bool = False) -> None:
        """Constructs an EcsPresenter object.

        Args:
            event (dict): the event from the API Gateway request to Lambda
            test (bool, optional): whether the task is being tested; defaults to False
        """

        self.ecsClient = boto3.client('ecs', region_name='us-west-2')

        self.ec2Client = boto3.client('ec2', region_name='us-west-2')
        self.securityGroupName = f'{PROJECT_NAME}-fargate-sg'

        self.s3 = S3Service()
        self.event = event

        envVar = EnvVar()
        self.PRIVATE_SUBNET_A_ID = envVar['PRIVATE_SUBNET_A_ID']
        self.PRIVATE_SUBNET_B_ID = envVar['PRIVATE_SUBNET_B_ID']
        self.VPC_ID = envVar['VPC_ID']

        parameterService = ParameterService()
        BugReporter.setVars(parameterService.getGithubCredentials(), PROJECT_NAME, 'byuawsfhtl', test)

    def _getTaskDefinitionArn(self) -> str:
        """Retrieves the task definition ARN with the latest revision number.

        Raises:
            Exception: no task definitions found for the cluster

        Returns:
            str: task definition ARN
        """
        response = self.ecsClient.list_task_definitions(familyPrefix=f'{PROJECT_NAME}-def', sort='DESC')
        arns = response['taskDefinitionArns']
        if len(arns) <= 0:
            raise Exception('No task definitions found for:', PROJECT_NAME)
        return arns[0]
    
    def _getSecGroupId(self) -> str:
        """Retrieves the security group ID for the cluster.

        Raises:
            Exception: couldn't find the security group

        Returns:
            str: security group ID
        """
        response = self.ec2Client.describe_security_groups(
            Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [self.VPC_ID]
                },
                {
                    'Name': 'group-name',
                    'Values': [self.securityGroupName]
                }
            ]
        )
        secGroups = response['SecurityGroups']
        if len(secGroups) <= 0:
            raise Exception("Couldn't find a security group with the name:", self.securityGroupName)
        secGroupId = secGroups[0]['GroupId']
        return secGroupId
    
    def _getVpcConfig(self) -> dict:
        """Retrieves the VPC configuration for the task.

        Returns:
            dict: the VPC configuration
        """
        secGroupId = self._getSecGroupId()
        vpcConfig = {
            'awsvpcConfiguration': {
                'subnets': [self.PRIVATE_SUBNET_A_ID, self.PRIVATE_SUBNET_B_ID],
                'securityGroups': [secGroupId]
            }
        }
        return vpcConfig
    
    def _reportBug(self, e: Exception) -> None:
        """Reports a bug to the BugReporter.

        Args:
            e (Exception): the exception to report
        """
        excType = type(e).__name__
        tb = traceback.extract_tb(sys.exc_info()[2])
        functionName = tb[-1][2]

        # title for bug report
        title = f"{PROJECT_NAME} had a {excType} error with the {functionName} function"

        # description for bug report
        description = f'Type: {excType}\nError text: {e}\nFunction Name: {functionName}\n\n{traceback.format_exc()}'
        description += f'\nEnvironment: {EnvVar()["ENV"]}'

        BugReporter.manualBugReport(title, description)

    def run(self) -> tuple[int, dict]:
        """Runs the task with the given key as an environment variable.
        
        Returns:
            tuple[int, dict]: 
                int: the status code
                dict: the response message
        """
        try:
            body = self.event['body']
            body = json.loads(body)
            self.key = body['inputFile']
            fileName = self.key.split('/')[-1]
            newKey = f'InProgress/{fileName}'
            self.s3.moveFile(self.key, newKey)

            response = self.ecsClient.run_task(
                cluster = PROJECT_NAME,
                count = 1,
                taskDefinition = self._getTaskDefinitionArn(),
                launchType = 'FARGATE',
                networkConfiguration = self._getVpcConfig(),
                overrides={
                    'containerOverrides': [
                        {
                            'name': f'{PROJECT_NAME}Container',
                            'environment': [
                                {
                                    'name': 'INFILE',
                                    'value': newKey
                                }
                            ]
                        }
                    ]
                }
            )
        except KeyError as e:
            print(traceback.format_exc())
            statusCode = 400
            response = {'error': 'No infile key provided in request body.'}
            self._reportBug(e)
        except FileNotFoundError as e:
            print(traceback.format_exc())
            statusCode = 404
            response = {'error': f'No file found for given infile key: {self.key}'}
            self._reportBug(e)
        except ClientError as e:
            print(traceback.format_exc())
            statusCode = 500
            response = {'error': 'Internal Server Error'}
            self._reportBug(e)
        except Exception as e:
            print(traceback.format_exc())
            statusCode = 500
            response = {'error': 'Internal Server Error'}
            self._reportBug(e)
        else:
            statusCode = 200
            response = {'message': f'Successfully started a task with the key: {newKey}'}
        finally:
            return statusCode, response
