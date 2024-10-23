from common.models.AwsSession import AwsSession

class S3Dao:
    """Contains methods for communicating with S3.

    Attributes:
        client: AWS client object for Amazon S3
    """
    
    def __init__(self) -> None:
        """Constructs an S3Dao object."""
        awsSession = AwsSession()
        session = awsSession.getSession()
        self.client = session.client(service_name='s3')

    def moveFile(self, oldBucket: str, oldKey: str, 
                destBucket: str, destKey: str) -> tuple[dict, dict]:
        """Moves file between S3 buckets.

        If the move is to the same bucket, then this is essentially a 
        'rename' operation.

        Args:
            oldBucket (str): name of bucket to move file from
            oldKey (str): key of original file
            destBucket (str): name of bucket to move file to
            destKey (str): key of destination file
        
        Returns:
            tuple[dict, dict]:
                dict: response of `S3.Client.copy_object` operation
                dict: response of `S3.Client.delete_object` operation
        """
        copyResponse = self.client.copy_object(
            Bucket=destBucket,
            Key=destKey,
            CopySource={
                'Bucket': oldBucket,
                'Key': oldKey
            }
        )
        delResponse = self.client.delete_object(
            Bucket=oldBucket,
            Key=oldKey
        )
        return copyResponse, delResponse
