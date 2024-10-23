from io import StringIO

from awsEcs.models.services.EcsS3Dao import EcsS3Dao
from common.models.services.S3Service import S3Service
from common.Names import NEXT_APP_NAME

class EcsS3Service(S3Service):
    """Contains methods for working with the input file.

    Attributes:
        s3Dao (S3Dao): DAO for accessing Amazon S3
        env (EnvVar): instance of EnvVar to access environment vars
        dataBucketName (str): name of S3 data bucket
        nextAppDataBucketName (str): name of next app's S3 data bucket
    """

    def __init__(self) -> None:
        """Constructs an EcsS3Service object."""
        super().__init__()
        self.nextAppDataBucketName = f'{NEXT_APP_NAME}-data-{self.env["ENV"]}'

    def _createS3Dao(self) -> EcsS3Dao:
        """Factory method to create S3Dao instance.

        Overrides parent's `_createS3Dao` method.
        
        Returns:
            EcsS3Dao: instance of EcsS3Dao
        """
        return EcsS3Dao()
        
    def readFile(self, key: str) -> StringIO:
        """Reads data from file in S3 data bucket.

        Args:
            key (str): key of file

        Returns:
            StringIO: hint data from file as string buffer
        """
        response: dict = self.s3Dao.readFile(self.dataBucketName, key)
        rawData: bytes = response['Body']
        fileContents = StringIO(rawData.read().decode('utf8'), newline=None) # 'newLine=None' means we use universal newlines support)
        return fileContents
    
    def writeOutputFile(self, data: StringIO, fileName: str) -> tuple[dict, dict]:
        """Writes data to output file in S3 bucket.

        This will write the output data to the current process's data bucket.
        Then, it will try to write data to the next process's data bucket.

        Args:
            data (StringIO): data to write to output file
            fileName (str): name of file (including its extension)

        Returns:
            tuple[dict, dict]:
                dict: response of `S3.Client.put_object` operation for data bucket
                dict: response of `S3.Client.put_object` operation for next process's data bucket
        """
        outKey = f'Output/{fileName}'
        outData: bytes = data.read().encode('utf8')
        response = self.s3Dao.writeFile(self.dataBucketName, outKey, outData)
        nextAppOutKey = f'ToDo/{fileName}'
        nextAppResponse = self.s3Dao.writeFile(self.nextAppDataBucketName, nextAppOutKey, outData)
        
        return response, nextAppResponse
