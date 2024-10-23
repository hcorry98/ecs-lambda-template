import json

from common.models.AwsSession import AwsSession

class ParameterService:
    """Gets parameters from Parameter Store.
    
    Attributes: 
        PYFS_PARAMETER_NAME (str): AWS Parameter Store parameter name for PyFS credentials
        GITHUB_PARAMETER_NAME (str): AWS Parameter Store parameter name for Github token
        client (boto3.Session.client): AWS client object for AWS Systems Manager Parameter Store
    """

    PYFS_PARAMETER_NAME = '/growth-spurt/DataFinder/credentials'
    GITHUB_PARAMETER_NAME = '/growth-spurt/github/access-token'
    
    def __init__(self) -> None:
        """Constructs a ParameterService object."""
        awsSession = AwsSession()
        session = awsSession.getSession()
        self.client = session.client(service_name='ssm')
        
    def _getParameter(self, parameterName: str) -> dict:
        """Gets a parameter from AWS Parameter Store.

        Args:
            parameterName (str): parameter name to get from AWS Parameter Store

        Returns:
            dict: parameter from AWS Parameter Store
        """
        response = self.client.get_parameter(
            Name=parameterName,
            WithDecryption=True
        )
        return response['Parameter']
    
    def getPyFSCredentials(self) -> dict:
        """Gets the PyFS GrowthSpurt key needed to run threaded PyFS calls.

        Returns:
            dict: the PyFS credentials for GrowthSpurt
        """
        parameter = self._getParameter(self.PYFS_PARAMETER_NAME)['Value']
        credentials = json.loads(parameter)
        return credentials
    
    def getGithubCredentials(self) -> str:
        """Gets the Github token needed to run threaded PyFS calls.

        Returns:
            str: github's token
        """
        token = self._getParameter(self.GITHUB_PARAMETER_NAME)['Value']
        return token
