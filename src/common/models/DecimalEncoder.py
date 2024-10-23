import json
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal objects."""
    
    def default(self, o: object) -> str:
        """Converts Decimal objects to strings to maintain accuracy and allow for json serialization.

        Args:
            o (object): the object to encode

        Returns:
            str: the encoded object
        """
        if isinstance(o, Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)
