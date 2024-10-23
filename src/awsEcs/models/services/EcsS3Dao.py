from common.models.services.S3Dao import S3Dao

class EcsS3Dao(S3Dao):
    """Contains methods for communicating with S3.

    Attributes:
        client: AWS client object for Amazon S3
    """
    
    def __init__(self) -> None:
        """Constructs an EcsS3Dao object."""
        super().__init__()

    def readFile(self, bucket: str, key: str) -> dict:
        """Returns file data from S3 bucket.

        Args:
            bucket (str): name of bucket to read file from
            key (str): key of file

        Returns:
            dict: response of `S3.Client.get_object` operation
        """
        response: dict = self.client.get_object(
            Bucket=bucket,
            Key=key
        )
        return response

    def writeFile(self, bucket: str, key: str, data: bytes) -> dict:
        """Puts file in S3 bucket.

        Args:
            bucket (str): name of bucket to put file in 
            key (str): key of file
            data (bytes): data of file 

        Returns:
            dict: response of `S3.Client.put_object` operation
        """
        response = self.client.put_object(
            Bucket=bucket,
            Key=key,
            Body=data
        )
        return response
