import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from awsLambda.presenters.Validator import ValidationException, Validator
from common.models.EnvVar import EnvVar
from common.Names import SUBDOMAIN

class TestValidatorUnit(unittest.TestCase):
    """Unit tests the Lambda Validator presenter class."""

    def setUp(self):
        """Sets up the test case."""
        self.validator = Validator()
        self.STG_DOMAIN = 'rll-dev.byu.edu'

        self.TEST_ENV = 'stg'
        self.validator.env = self.TEST_ENV

        osEnv = {
            'ENV': self.TEST_ENV
        } 
        os.environ.update(osEnv)

    def tearDown(self):
        """Tears down the test case."""
        del os.environ['ENV']

    # validate Tests
    @patch('awsLambda.presenters.Validator.Validator.getOrigin')
    @patch('awsLambda.presenters.Validator.Validator.getDomain')
    @patch('awsLambda.presenters.Validator.Validator.validateRequest')
    def test_validate(self, mock_validateRequest, mock_getDomain, mock_getOrigin):
        """Ensure the validate method returns the correct response."""
        event = {}
        origin = f'https://{SUBDOMAIN}.{self.STG_DOMAIN}'
        mock_getOrigin.return_value = origin
        mock_getDomain.return_value = self.STG_DOMAIN
        mock_validateRequest.return_value = None

        with redirect_stdout(None):
            resp = self.validator.validate(event)

        self.assertEqual(resp, (200, {'message': 'Request comes from a valid source.'}))

        EnvVar.delete()

    @patch('awsLambda.presenters.Validator.Validator.getOrigin')
    @patch('awsLambda.presenters.Validator.Validator.getDomain')
    @patch('awsLambda.presenters.Validator.Validator.validateRequest')
    def test_validate_error(self, mock_validateRequest, mock_getDomain, mock_getOrigin):
        """Ensure the validate method returns the correct response when an exception is raised."""
        event = {}
        origin = f'https://{SUBDOMAIN}.{self.STG_DOMAIN}'
        mock_getOrigin.return_value = origin
        mock_getDomain.return_value = self.STG_DOMAIN
        mock_validateRequest.side_effect = ValidationException('test error')

        with redirect_stdout(None):
            resp = self.validator.validate(event)

        self.assertEqual(resp, (403, {'error': 'test error'}))

        EnvVar.delete()

    # getOrigin Tests
    def test_getOrigin(self):
        """Ensure the getOrigin method returns the correct origin."""
        expectedOrigin = f'https://{SUBDOMAIN}.{self.STG_DOMAIN}'
        event = {'headers': {'Origin': expectedOrigin}}

        origin = Validator.getOrigin(event)

        self.assertEqual(origin, expectedOrigin)

    def test_getOrigin_capitalized(self):
        """Ensure the getOrigin method returns the correct origin when the origin is capitalized."""
        expectedOrigin = f'https://{SUBDOMAIN}.{self.STG_DOMAIN}'
        event = {'headers': {'ORigIn': f'https://{SUBDOMAIN}.RLL-DEV.bYu.EdU'}}

        origin = Validator.getOrigin(event)

        self.assertEqual(origin, expectedOrigin)

    def test_getOrigin_noOrigin(self):
        """Ensure the getOrigin method raises an exception when the origin is not in the headers."""
        event = {'headers': {}}

        with self.assertRaises(KeyError):
            Validator.getOrigin(event)

    def test_getOrigin_noHeaders(self):
        """Ensure the getOrigin method raises an exception when the headers are not in the event."""
        event = {}

        with self.assertRaises(KeyError):
            Validator.getOrigin(event)

    # getDomain Tests
    def test_getDomain(self):
        """Ensure the getDomain method returns the correct domain."""
        origin = f'https://{SUBDOMAIN}.{self.STG_DOMAIN}'

        domain = self.validator.getDomain(origin)

        self.assertEqual(domain, self.STG_DOMAIN)

    def test_getDomain_wrongSubdomain(self):
        """Ensure the getDomain method returns the correct domain even when the subdomain doesn't match the project."""
        origin = f'https://wrong.{self.STG_DOMAIN}'

        domain = self.validator.getDomain(origin)
        self.assertEqual(domain, self.STG_DOMAIN)

    def test_getDomain_wrongEnv(self):
        """Ensure the getDomain method raises an exception when the environment does not match the domain."""
        self.validator.env = 'prd'
        origin = f'https://{SUBDOMAIN}.{self.STG_DOMAIN}'

        with self.assertRaises(ValidationException):
            self.validator.getDomain(origin)

    def test_getDomain_wrongDomain(self):
        """Ensure the getDomain method raises an exception when the domain is not allowed."""
        origin = f'https://{SUBDOMAIN}.example.com'

        with self.assertRaises(ValidationException):
            self.validator.getDomain(origin)

    def test_getDomain_noOrigin(self):
        """Ensure the getDomain method raises an exception when the origin is None."""
        origin = None

        with self.assertRaises(ValidationException):
            self.validator.getDomain(origin)

    def test_getDomain_noHostname(self):
        """Ensure the getDomain method raises an exception when the origin does not have a hostname."""
        origin = ''

        with self.assertRaises(AttributeError):
            self.validator.getDomain(origin)

    # validateRequest Tests
    def test_validateRequest(self):
        """Ensure the validateRequest method returns when the request is valid."""
        origin = f'https://{SUBDOMAIN}.{self.STG_DOMAIN}'
        try:
            self.validator.validateRequest(origin, self.STG_DOMAIN)
        except:
            self.fail('validateRequest raised an exception when the request was valid.')

    def test_validateRequest_invalidOrigin(self):
        """Ensure the validateRequest method raises an exception when the origin does not match."""
        origin = f'https://{SUBDOMAIN}.rll.byu.edu'

        with self.assertRaises(ValidationException):
            self.validator.validateRequest(origin, self.STG_DOMAIN)

    def test_validateRequest_invalidSubdomain(self):
        """Ensure the validateRequest method raises an exception when the subdomain is invalid."""
        origin = f'https://wrong.{self.STG_DOMAIN}'

        with self.assertRaises(ValidationException):
            self.validator.validateRequest(origin, self.STG_DOMAIN)
        
        EnvVar.delete()

    def test_validateRequest_invalidDomain(self):
        """Ensure the validateRequest method raises an exception when the domain is invalid."""
        origin = f'https://{SUBDOMAIN}.{self.STG_DOMAIN}'
        domain = 'example.com'

        with self.assertRaises(ValidationException):
            self.validator.validateRequest(origin, domain)

    # sendCorsResponse Tests
    def test_sendCorsResponse(self):
        """Ensure the sendCorsResponse method returns the correct response."""
        origin = f'https://{SUBDOMAIN}.{self.STG_DOMAIN}'
        statusCode = 200
        response = {'test': 'response'}
        expectedResponse = {
            'statusCode': statusCode,
            'headers': {'Access-Control-Allow-Origin': origin,},
            'body': '{"test": "response"}'
        }

        with redirect_stdout(None):
            resp = self.validator.sendCorsResponse(origin, statusCode, response)

        self.assertEqual(resp, expectedResponse)

    def test_sendCorsResponse_error(self):
        """Ensure the sendCorsResponse method returns the correct response when the status code is an error."""
        origin = f'https://{SUBDOMAIN}.{self.STG_DOMAIN}'
        statusCode = 400
        response = {'error': 'response'}
        expectedResponse = {
            'statusCode': statusCode,
            'headers': {'Access-Control-Allow-Origin': origin,},
            'body': '{"error": "response"}'
        }

        with redirect_stdout(None):
            resp = self.validator.sendCorsResponse(origin, statusCode, response)

        self.assertEqual(resp, expectedResponse)

    def test_sendCorsResponse_emptyResponse(self):
        """Ensure the sendCorsResponse method returns the correct response when the response is empty."""
        origin = f'https://{SUBDOMAIN}.{self.STG_DOMAIN}'
        statusCode = 200
        response = {}
        expectedResponse = {
            'statusCode': statusCode,
            'headers': {'Access-Control-Allow-Origin': origin,},
            'body': '{}'
        }

        with redirect_stdout(None):
            resp = self.validator.sendCorsResponse(origin, statusCode, response)

        self.assertEqual(resp, expectedResponse)
