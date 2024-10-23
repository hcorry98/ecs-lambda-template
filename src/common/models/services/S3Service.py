from botocore.exceptions import ClientError

from common.models.EnvVar import EnvVar
from common.models.services.S3Dao import S3Dao
from common.Names import APP_NAME

class S3Service:
    """Contains methods for working with the input file.

    Attributes:
        s3Dao (S3Dao): DAO for accessing Amazon S3
        env (EnvVar): instance of EnvVar to access environment vars
        dataBucketName (str): name of S3 data bucket
    """

    def __init__(self) -> None:
        """Constructs an S3Service object."""
        self.s3Dao: S3Dao = self._createS3Dao()
        self.env = EnvVar()
        self.dataBucketName = f'{APP_NAME}-data-{self.env["ENV"]}'
        
    def _createS3Dao(self) -> S3Dao:
        """Factory method to create S3Dao instance.
        
        Returns:
            S3Dao: instance of S3Dao
        """
        return S3Dao()

    def _isNonexistentFileError(self, e: ClientError) -> bool:
        """Determines if ClientError is due to file not existing or not.
        
        Args:
            e (ClientError): error to check

        Returns:
            bool: whether or not error is due to file not existing 
        """
        NONEXISTENT_FILE_CODE = 'InvalidArgument' # AWS says the given file key is "invalid" when it doesn't exist
        NO_SUCH_KEY_CODE = 'NoSuchKey' # AWS says the given file key doesn't exist
        if e.response['Error']['Code'] == NONEXISTENT_FILE_CODE or e.response['Error']['Code'] == NO_SUCH_KEY_CODE:
            return True
        else:
            return False
    
    def moveFile(self, oldKey: str, newKey: str) -> tuple[dict, dict]:
        """Moves file in S3 bucket. 

        Args:
            oldKey (str): key to where file is located
            newKey (str): key to where file will be moved

        Raises:
            FileNotFoundError: if file does not exist

        Returns:
            tuple[dict, dict]:
                dict: response of `S3.Client.copy_object` operation
                dict: response of `S3.Client.delete_object` operation
        """
        try:
            return self.s3Dao.moveFile(self.dataBucketName, oldKey, self.dataBucketName, newKey)
        except ClientError as e:
            if self._isNonexistentFileError(e):
                raise FileNotFoundError(e)
            else: 
                raise e
