import boto3

class AwsSession:
    """Singleton class for the AWS session.
    
    Attributes:
        AWS_REGION (str): the AWS region
        session (boto3.Session): the AWS session to use
    """

    AWS_REGION = 'us-west-2'

    def __new__(awsSession: 'AwsSession') -> 'AwsSession':
        """Returns an instance of AwsSession.
        
        If one does not already exist, creates a new one; 
        otherwise, returns the existing instance.

        Args:
            awsSession (AwsSession): the class

        Returns:
            AwsSession: the instance of the class
        """
        if not hasattr(awsSession, 'instance'):
            awsSession.instance = super(AwsSession, awsSession).__new__(awsSession)

            # Initialize the class only once and initialize the AWS session
            awsSession.instance.session = AwsSession._initSession()

        return awsSession.instance
    
    @classmethod
    def _initSession(cls) -> boto3.Session:
        """Initializes an AWS session.
        
        Returns:
            boto3.Session: the AWS session
        """
        session = boto3.Session(region_name=cls.AWS_REGION)
        return session
    
    def getSession(self) -> boto3.Session:
        """Gets the AWS session.

        Returns:
            boto3.Session: the AWS session
        """
        return self.session
