import boto3
from pathlib import Path
from botocore.exceptions import ClientError
import logging

class S3Service:

    def __init__(self, bucket_name:str, session:boto3.Session = None, logger:logging.Logger=None):
        self.bucket_name=bucket_name
        self.session = session or boto3.Session()
        self.logger = logger or logging.getLogger(__name__)

        self.s3 = self.session.resource("s3")
        self.bucket = self.s3.Bucket(bucket_name) 


    def list_files(self, prefix:str="") -> list[str]:
        try:
            return [obj.key for obj in self.bucket.objects.filter(Prefix=prefix)]
        except ClientError as e:
            self.logger.error("List failed: %s", e)
            raise

    def upload_file(self, local_path: Path, s3_key: str) -> None:
        try:
            self.logger.info("Uploading %s to s3://%s/%s", local_path, self.bucket_name, s3_key)
            self.bucket.upload_file(str(local_path), s3_key)
        except ClientError as e:
            self.logger.error("Upload failed: %s", e)
            raise    
    
    def download_file(self, s3_key: str, local_path: Path, overwrite:bool=False) -> Path:
        try:
            if local_path.exists() and not overwrite:
                self.logger.info("File already exists, skipping: %s", local_path)
                return local_path
            self.logger.info("Downloading s3://%s/%s to %s", self.bucket_name, s3_key, local_path)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            self.bucket.download_file(s3_key, str(local_path))
            return local_path
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                self.logger.error("File not found in S3: %s", s3_key)
            else:
                self.logger.error("Download failed: %s", e)
            raise

    def delete_file(self, s3_key: str) -> None:
        try:
            self.logger.info("Deleting s3://%s/%s", self.bucket_name, s3_key)
            self.bucket.Object(s3_key).delete()
        except ClientError as e:
            self.logger.error("Delete failed: %s", e)
            raise