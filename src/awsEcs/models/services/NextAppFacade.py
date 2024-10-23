import requests

from common.Names import NEXT_APP_SUBDOMAIN

class NextAppFacade:
    """Contains a method for running the next application.
    
    Attributes:
        NEXT_GS_RUN_ENDPOINT (str): API endpoint for running next app 
        ORIGIN (str): origin for the request to run next app
    """

    def __init__(self, env: str) -> None:
        """Constructs a NextAppFacade object.
        
        Args:
            env (str): version of next app to run
        """
        if env == 'prd':
            subdomainEnv = 'rll'
        elif env in ['dev', 'stg']:
            subdomainEnv = 'rll-dev'
        else:
            subdomainEnv = f'rll-{env}'

        self.NEXT_GS_RUN_ENDPOINT = f'https://api.{NEXT_APP_SUBDOMAIN}.{subdomainEnv}.byu.edu/run'
        self.ORIGIN = f'https://{NEXT_APP_SUBDOMAIN}.{subdomainEnv}.byu.edu'

    def run(self, infile: str) -> None:
        """Starts next app by calling its API, passing the key of the infile.

        Args:
            infile (str): key of input file in next app's S3 bucket
        """
        res = requests.post(
            self.NEXT_GS_RUN_ENDPOINT,
            json={'inputFile': infile},
            headers={'origin': self.ORIGIN}
        )
        if res.status_code != 200:
            print('\nError running next app:')
            print(f'Status code: {res.status_code}')
            print(f'Response: {res.text}')
        else:
            print('Next app ran successfully!')
