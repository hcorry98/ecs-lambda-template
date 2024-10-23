from io import StringIO

import pandas as pd
from PyBugReporter.src.BugReporter import BugReporter

from awsEcs.models.services.EcsS3Service import EcsS3Service
from awsEcs.models.services.NextAppFacade import NextAppFacade
from common.models.EnvVar import EnvVar
from common.models.services.ParameterService import ParameterService
from common.Names import PROJECT_NAME

class EcsTask:
    """Contains methods for running the ECS task.

    Attributes:
        INFILE_KEY (str): key of input file
        INFILE_NAME (str): name of input file
        s3 (EcsS3Service): service for working with Amazon S3
        nextAppFacade (NextAppFacade): facade for running the next application
    """

    def __init__(self, test: bool = False) -> None:
        """Constructs an ECS Task object.
        
        Args:
            test (bool, optional): whether the task is being tested; defaults to False
        """
        envVar = EnvVar()

        self.INFILE_KEY: str = envVar['INFILE']
        self.INFILE_NAME: str = self.INFILE_KEY.split('/')[-1]
        env: str = envVar['ENV']
        env = env.lower()
        
        self.s3 = EcsS3Service()
        self.nextAppFacade = NextAppFacade(env)
        parameterService = ParameterService()
        BugReporter.setVars(parameterService.getGithubCredentials(), PROJECT_NAME, 'byuawsfhtl', test)

    @BugReporter(extraInfo=True, env=EnvVar()['ENV'], infile=EnvVar()['INFILE'])
    def run(self) -> None:
        """Runs the ECS Task."""
        print(f'\nLoading data from input file ({self.INFILE_KEY})...')
        inCsvData: StringIO = self.s3.readFile(self.INFILE_KEY)
        df: pd.DataFrame = pd.read_csv(inCsvData)

        # print('\nProcessing hints...')
        # TODO: process data
        outData = df

        print('\nWriting hints to output bucket...')
        outBuffer = StringIO(outData.to_csv(index=False))
        self.s3.writeOutputFile(outBuffer, self.INFILE_NAME)

        print(f'\nMoving {self.INFILE_NAME} to "Done" folder...')
        outKey: str = f'Done/{self.INFILE_NAME}'
        self.s3.moveFile(self.INFILE_KEY, outKey)

        print('\nRunning the next application...')
        outKey: str = f'ToDo/{self.INFILE_NAME}'
        self.nextAppFacade.run(outKey)
