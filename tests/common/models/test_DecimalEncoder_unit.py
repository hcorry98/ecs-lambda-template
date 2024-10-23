import json
import unittest
from decimal import Decimal

from common.models.DecimalEncoder import DecimalEncoder

class TestDecimalEncoderUnit(unittest.TestCase):
    """Unit tests the Lambda DecimalEncoder model class."""

    def test_default_noDecimals(self):
        """Ensure the default method works with no decimals."""
        mockDict = {
            'key1': 'someString',
            'key2': 40.5,
            'key3': 40
        }

        self.assertEqual(json.dumps(mockDict, cls=DecimalEncoder), json.dumps(mockDict))

    def test_default_oneDecimal(self):
        """Ensure the default method works with one decimal."""
        mockDict = {
            'key1': 'someString',
            'key2': 40.5,
            'key3': Decimal(float(40.2)),
            'key4': 40
        }
        self.assertRaises(TypeError, json.dumps, mockDict)

        mockJson = '{"key1": "someString", "key2": 40.5, "key3": "40.2000000000000028421709430404007434844970703125", "key4": 40}'

        self.assertEqual(json.dumps(mockDict, cls=DecimalEncoder), mockJson)

    def test_default_manyDecimals(self):
        """Ensure the default method works with many decimals."""
        mockDict = {
            'key1': Decimal(0.1),
            'key2': 'someString',
            'key3': 40.5,
            'key4': Decimal(float(40.2)),
            'key5': 40,
            'key6': Decimal(1000)
        }
        self.assertRaises(TypeError, json.dumps, mockDict)

        mockJson = '{"key1": "0.1000000000000000055511151231257827021181583404541015625", '
        mockJson += '"key2": "someString'
        mockJson += '", "key3": 40.5, '
        mockJson += '"key4": "40.2000000000000028421709430404007434844970703125", '
        mockJson += '"key5": 40, '
        mockJson += '"key6": "1000"}'

        self.assertEqual(json.dumps(mockDict, cls=DecimalEncoder), mockJson)
