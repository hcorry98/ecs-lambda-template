import json
import traceback
from urllib.parse import urlparse

from common.models.DecimalEncoder import DecimalEncoder
from common.models.EnvVar import EnvVar
from common.Names import SUBDOMAIN

class ValidationException(Exception):
    """Exception for validation errors."""
    pass

class Validator(object):
    """Validates that the request comes from an allowed origin.

    Attributes:
        DEV_DOMAIN (str): the domain for the development environment
        PRD_DOMAIN (str): the domain for the production environment
        allowedDomains (list): the allowed domains for the project
    """

    DEV_DOMAIN = "rll-dev.byu.edu"
    PRD_DOMAIN = "rll.byu.edu"
    allowedDomains = [DEV_DOMAIN, PRD_DOMAIN]

    def validate(self, event: dict) -> tuple[int, dict]:
        """Validates that the request comes from an allowed origin.

        Args:
            event (dict): the event from the API Gateway request to Lambda

        Returns:
            tuple[int, dict]: 
                int: the status code
                dict: the response message
        """
        envVar = EnvVar()
        self.env = envVar['ENV']

        try:
            origin = Validator.getOrigin(event)
            domain = self.getDomain(origin)
            self.validateRequest(origin, domain)
            return 200, {'message': 'Request comes from a valid source.'}
        except ValidationException as e:
            print(traceback.format_exc())
            return 403, {'error': str(e)}

    @staticmethod
    def getOrigin(event: dict) -> str:
        """Gets the origin from the request headers.

        Args:
            event (dict): the event from the API Gateway request to Lambda

        Returns:
            str: the origin from the request headers
        """
        caseInsensitiveEvent = dict((key.lower(), event[key]) for key in event)
        headers = caseInsensitiveEvent['headers']

        caseInsensitiveHeaders = dict((key.lower(), headers[key]) for key in headers)
        origin = caseInsensitiveHeaders['origin'].lower()

        return origin

    def getDomain(self, origin: str) -> str:
        """Gets the domain from the origin.

        Args:
            origin (str): the origin from the request headers

        Raises:
            ValidationException: either no origin provided in request, 
                                 the request does not come from the current environment, 
                                 or the request does not come from an allowed domain

        Returns:
            str: the domain from the origin
        """
        if (origin is None):
            raise ValidationException('No origin provided in request. Origin is None.')

        hostname = urlparse(origin).hostname

        if (hostname.endswith(self.DEV_DOMAIN)):
            if self.env != 'stg':
                raise ValidationException(f'Request does not come from the current environment ({self.env}): {origin}')
            return self.DEV_DOMAIN
        elif (hostname.endswith(self.PRD_DOMAIN)):
            if self.env != 'prd':
                raise ValidationException(f'Request does not come from the current environment ({self.env}): {origin}')
            return self.PRD_DOMAIN
        else:
            raise ValidationException(f'Request does not come from an allowed domain: {origin}')

    def validateRequest(self, origin: str, domain: str) -> None:
        """Validates that the request comes from an allowed origin.

        If no exception is raised, the request is valid.

        Args:
            origin (str): the origin from the request headers
            domain (str): the domain from the origin

        Raises:
            ValidationException: the request does not come from an allowed origin
        """
        if not (origin == 'https://' + SUBDOMAIN + '.' + domain):
            raise ValidationException(f'Request does not come from an allowed origin: {origin}')

    def sendCorsResponse(self, origin: str, statusCode: int, response: dict) -> dict:
        """Sends a response with CORS headers.

        Args:
            origin (str): the origin from the request headers
            statusCode (int): the status code from the Lambda function
            response (dict): the response from the Lambda function

        Returns:
            dict: the response with CORS headers
        """
        responseMsg = {
            'statusCode': statusCode,
            'headers': {'Access-Control-Allow-Origin': origin},
            'body': json.dumps(response, cls=DecimalEncoder)
        }
        print(responseMsg)
        return responseMsg
