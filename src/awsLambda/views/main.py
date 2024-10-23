import sys, os
currentDir = os.path.dirname(os.path.realpath(__file__))
src = os.path.dirname(os.path.dirname(currentDir))
sys.path.append(src)

from awsLambda.presenters.Validator import Validator
from awsLambda.views.RunEcsTask import RunEcsTask

validator = Validator()

def handle_runEcsTask(event: dict, context: dict) -> dict:
    """Runs an ECS Task with the input file from the API Gateway request.

    Args:
        event (dict): the event from the API Gateway request to Lambda
        context (dict): the context of the Lambda function

    Returns:
        dict: the response from starting the ECS Task
    """
    return RunEcsTask(event, validator).handle()

# # For testing while an app is in development. Once out of development, remove this block:
# event = {
#     'headers': {
#         'origin': 'https://projectname.rll-dev.byu.edu'
#     }, 
#     'body': '{"inputFile":""}'
# }
# context = {}
# handle_runEcsTask(event, context)
