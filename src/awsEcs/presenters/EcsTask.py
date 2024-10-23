from io import StringIO

import pandas as pd

from awsEcs.models.services.EcsS3Service import EcsS3Service
from awsEcs.models.services.NextAppFacade import NextAppFacade
from common.models.EnvVar import EnvVar

class EcsTask:
    """Contains methods for running the ECS task.

    Attributes:
        INFILE_KEY (str): key of input file
        INFILE_NAME (str): name of input file
        s3 (EcsS3Service): service for working with Amazon S3
        nextAppFacade (NextAppFacade): facade for running the next application
    """

    def __init__(self) -> None:
        """Constructs an ECS Task object."""
        envVar = EnvVar()

        self.INFILE_KEY: str = envVar['INFILE']
        self.INFILE_NAME: str = self.INFILE_KEY.split('/')[-1]
        env: str = envVar['ENV']
        env = env.lower()
        
        self.s3 = EcsS3Service()
        self.nextAppFacade = NextAppFacade(env)

    def run(self) -> None:
        """Runs the ECS Task."""
        print(f'\nLoading data from input file ({self.INFILE_KEY})...')
        inCsvData: StringIO = self.s3.readFile(self.INFILE_KEY)
        df = pd.read_csv(inCsvData)

        # print('\nProcessing hints...')
        # TODO: process data
        outData = df

        print('\nWriting hints to output bucket...')
        outBuffer = StringIO(outData.to_csv())
        self.s3.writeOutputFile(outBuffer, self.INFILE_NAME)

        print('\nMoving input file to "Done" folder...')
        outKey: str = f'Done/{self.INFILE_NAME}'
        self.s3.moveFile(self.INFILE_KEY, outKey)

        print('\nRunning the next application...')
        outKey: str = f'ToDo/{self.INFILE_NAME}'
        self.nextAppFacade.run(outKey)
