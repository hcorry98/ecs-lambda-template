import json
import traceback

import boto3
from botocore.exceptions import ClientError

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

    PRIVATE_SUBNET_A_ID = 'subnet-04ea1b1ec5d896375'
    PRIVATE_SUBNET_B_ID = 'subnet-0a9cdc5582a7a6e20'
    VPC_ID = 'vpc-057175f829f9e74b2'
     
    def __init__(self, event: dict) -> None:
        """Constructs an EcsPresenter object.

        Args:
            event (dict): the event from the API Gateway request to Lambda
        """

        self.ecsClient = boto3.client('ecs', region_name='us-west-2')

        self.ec2Client = boto3.client('ec2', region_name='us-west-2')
        self.securityGroupName = f'{PROJECT_NAME}-fargate-sg'

        self.s3 = S3Service()
        
        self.event = event

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
        except FileNotFoundError as e:
            print(traceback.format_exc())
            statusCode = 404
            response = {'error': f'No file found for given infile key: {self.key}'}
        except ClientError as e:
            print(traceback.format_exc())
            statusCode = 500
            response = {'error': 'Internal Server Error'}
        except:
            print(traceback.format_exc())
            statusCode = 500
            response = {'error': 'Internal Server Error'}
        else:
            statusCode = 200
            response = {'message': f'Successfully started a task with the key: {newKey}'}
        finally:
            return statusCode, response
