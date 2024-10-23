import traceback

from awsLambda.presenters.Validator import Validator

class Handle:
    """An abstract base class responsible for handling the event and validation for all the views.

    No changes need to be made to this class from the template. When a new endpoint is created,
    a new subclass should be created to override the _run method. The _run method is responsible
    for calling the presenter of the endpoint.

    This class is meant to implement the Template Method pattern. The _run method is the abstract
    method that must be implemented.

    Attributes:
        event (dict): the event dictionary from the lambda function
        validator (Validator): the validator object that will be used to validate the event
    """
    
    def __init__(self, event: dict, validator: Validator) -> None:
        """Initializes the Handle.

        Args:
            event (dict): the event dictionary from the lambda function
            validator (Validator): the validator object that will be used to validate the event
        """
        self.event = event
        self.validator = validator

    def handle(self, *args) -> dict:
        """Handles the validation and response of the event.

        Args:
            *args: the arguments to be passed to the _run method

        Returns:
            dict: the HTTP response
        """
        print('Event:', self.event)
        origin = Validator.getOrigin(self.event)
        try:
            statusCode, response = self.validator.validate(self.event)
            if statusCode != 200:
                return self.validator.sendCorsResponse(origin, statusCode, response)

            statusCode, response = self._run(*args)

            return self.validator.sendCorsResponse(origin, statusCode, response)
        except:
            print(traceback.format_exc())
            return self.validator.sendCorsResponse(origin, 500, {'error': 'Internal Server Error'})

    def _run(self, *args) -> tuple[int, dict]:
        """The function to be overridden by the subclass.
        
        This function is responsible for calling the presenter of the endpoint.

        Args:
            *args: the arguments to be passed to the presenter

        Raises:
            NotImplementedError: the subclass must implement this method

        Returns:
            tuple[int, dict]: 
                int: the status code
                dict: response from running the Handle
        """
        raise NotImplementedError('Subclasses must implement this method.')
