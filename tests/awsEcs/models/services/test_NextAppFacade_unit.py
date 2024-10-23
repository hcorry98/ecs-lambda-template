from contextlib import redirect_stdout
from unittest import TestCase
from unittest.mock import patch

from awsEcs.models.services.NextAppFacade import NextAppFacade
from common.Names import NEXT_APP_SUBDOMAIN

class TestNextAppFacadeUnit(TestCase):
    """Unit tests for NextAppFacade."""
    
    TEST_ENV = 'stg'
    testFileKey = "bucket/key"
    STG_DOMAIN = 'rll-dev.byu.edu'
    PRD_DOMAIN = 'rll.byu.edu'

    def test_constructor_dev(self):
        """Tests if NextAppFacade can be successfully initialized in a dev environment."""
        nextAppFacade = NextAppFacade('dev')

        expectedEndpoint = f'https://api.{NEXT_APP_SUBDOMAIN}.{self.STG_DOMAIN}/run'
        expectedOrigin = f'https://{NEXT_APP_SUBDOMAIN}.{self.STG_DOMAIN}'

        self.assertEqual(nextAppFacade.NEXT_GS_RUN_ENDPOINT, expectedEndpoint)
        self.assertEqual(nextAppFacade.ORIGIN, expectedOrigin)

    def test_constructor_stg(self):
        """Tests if NextAppFacade can be successfully initialized in a stg environment."""
        nextAppFacade = NextAppFacade('stg')

        expectedEndpoint = f'https://api.{NEXT_APP_SUBDOMAIN}.{self.STG_DOMAIN}/run'
        expectedOrigin = f'https://{NEXT_APP_SUBDOMAIN}.{self.STG_DOMAIN}'

        self.assertEqual(nextAppFacade.NEXT_GS_RUN_ENDPOINT, expectedEndpoint)
        self.assertEqual(nextAppFacade.ORIGIN, expectedOrigin)

    def test_constructor_prd(self):
        """Tests if NextAppFacade can be successfully initialized in a prd environment."""
        nextAppFacade = NextAppFacade('prd')

        expectedEndpoint = f'https://api.{NEXT_APP_SUBDOMAIN}.{self.PRD_DOMAIN}/run'
        expectedOrigin = f'https://{NEXT_APP_SUBDOMAIN}.{self.PRD_DOMAIN}'

        self.assertEqual(nextAppFacade.NEXT_GS_RUN_ENDPOINT, expectedEndpoint)
        self.assertEqual(nextAppFacade.ORIGIN, expectedOrigin)

    def test_constructor_invalid(self):
        """Tests if NextAppFacade can be successfully initialized with an invalid environment."""
        nextAppFacade = NextAppFacade('invalid')

        expectedEndpoint = f'https://api.{NEXT_APP_SUBDOMAIN}.rll-invalid.byu.edu/run'
        expectedOrigin = f'https://{NEXT_APP_SUBDOMAIN}.rll-invalid.byu.edu'

        self.assertEqual(nextAppFacade.NEXT_GS_RUN_ENDPOINT, expectedEndpoint)
        self.assertEqual(nextAppFacade.ORIGIN, expectedOrigin)
        
    @patch('awsEcs.models.services.NextAppFacade.requests')
    def test_run(self, mockRequests):
        """Tests if NextAppFacade can be successfully run."""
        nextAppFacade = NextAppFacade(self.TEST_ENV)

        with redirect_stdout(None):
            nextAppFacade.run(self.testFileKey)

        mockRequests.post.assert_called_once()
        mockRequests.post.assert_called_with(
            f'https://api.{NEXT_APP_SUBDOMAIN}.{self.STG_DOMAIN}/run', 
            json={ 'inputFile': self.testFileKey },
            headers={ 'origin': f'https://{NEXT_APP_SUBDOMAIN}.{self.STG_DOMAIN}' }
        )
