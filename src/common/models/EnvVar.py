import os
from pathlib import Path

import environ

class EnvVar(object):
    """Singleton class for environment variables."""
    
    def __new__(envVar: "EnvVar") -> "EnvVar":
        """Returns an instance of EnvVar.
        
        If one does not already exist, creates a new one; 
        otherwise, returns the existing instance. If a new 
        instance is created, the .env file is loaded.

        Args:
            envVar (EnvVar): the class

        Returns:
            EnvVar: the instance of the class
        """
        if not hasattr(envVar, 'instance'):
            envVar.instance = super(EnvVar, envVar).__new__(envVar)

            # Initialize the class only once and load the .env file
            envVar.instance.envir = environ.Env()
            envPath = os.path.join(Path(__file__).resolve().parent.parent, '.env')
            environ.Env.read_env(envPath)

        return envVar.instance
    
    def __call__(self, key: str) -> str:
        """Allows the class to be called as a function.

        Args:
            key (str): the name of the environment variable

        Returns:
            str: the value of the environment variable
        """
        return self.envir(key)
    
    def __getitem__(self, key: str) -> str:
        """Allows the class to be accessed like a dictionary.

        Args:
            key (str): the name of the environment variable

        Returns:
            str: the value of the environment variable
        """
        return self.envir(key)
    
    @classmethod
    def delete(cls) -> None:
        """Deletes instance attribute allowing future constructor calls to reinitialize the singleton.
        
        If instance attribute doesn't exist, returns without error.
        """
        if hasattr(cls, 'instance'):
            del cls.instance
