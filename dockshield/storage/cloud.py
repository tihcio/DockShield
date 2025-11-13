"""
Cloud storage backends for DockShield (S3, Azure, Google Cloud)
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from dockshield.storage.base import StorageBackend

logger = logging.getLogger(__name__)


class S3Storage(StorageBackend):
    """AWS S3 storage backend"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize S3 storage

        Args:
            config: Storage configuration
        """
        super().__init__(config)
        self.bucket = config.get("bucket")
        self.region = config.get("region", "us-east-1")
        self.prefix = config.get("prefix", "dockshield/")
        self.storage_class = config.get("storage_class", "STANDARD")

        # AWS credentials (optional, can use IAM role)
        self.access_key_id = config.get("access_key_id")
        self.secret_access_key = config.get("secret_access_key")

        self.s3_client = None

    def connect(self) -> bool:
        """
        Connect to S3

        Returns:
            True if successful, False otherwise
        """
        try:
            import boto3

            # Create S3 client
            if self.access_key_id and self.secret_access_key:
                self.s3_client = boto3.client(
                    "s3",
                    region_name=self.region,
                    aws_access_key_id=self.access_key_id,
                    aws_secret_access_key=self.secret_access_key,
                )
            else:
                # Use IAM role or environment variables
                self.s3_client = boto3.client("s3", region_name=self.region)

            # Test connection
            self.s3_client.head_bucket(Bucket=self.bucket)

            logger.info(f"Connected to S3 bucket: {self.bucket}")
            return True

        except ImportError:
            logger.error("boto3 not installed. Install with: pip install boto3")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to S3: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from S3"""
        self.s3_client = None

    def is_connected(self) -> bool:
        """Check if connected to S3"""
        return self.s3_client is not None

    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """Upload file to S3"""
        try:
            if not self.s3_client:
                logger.error("Not connected to S3")
                return False

            key = f"{self.prefix}{remote_path}"

            self.s3_client.upload_file(
                str(local_path),
                self.bucket,
                key,
                ExtraArgs={"StorageClass": self.storage_class}
            )

            logger.debug(f"Uploaded {local_path} to s3://{self.bucket}/{key}")
            return True

        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            return False

    def download_file(self, remote_path: str, local_path: Path) -> bool:
        """Download file from S3"""
        try:
            if not self.s3_client:
                logger.error("Not connected to S3")
                return False

            key = f"{self.prefix}{remote_path}"
            local_path.parent.mkdir(parents=True, exist_ok=True)

            self.s3_client.download_file(self.bucket, key, str(local_path))

            logger.debug(f"Downloaded s3://{self.bucket}/{key} to {local_path}")
            return True

        except Exception as e:
            logger.error(f"Error downloading from S3: {e}")
            return False

    def delete_file(self, remote_path: str) -> bool:
        """Delete file from S3"""
        try:
            if not self.s3_client:
                logger.error("Not connected to S3")
                return False

            key = f"{self.prefix}{remote_path}"
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)

            logger.debug(f"Deleted s3://{self.bucket}/{key}")
            return True

        except Exception as e:
            logger.error(f"Error deleting from S3: {e}")
            return False

    def list_files(self, remote_path: str = "") -> List[str]:
        """List files in S3"""
        try:
            if not self.s3_client:
                logger.error("Not connected to S3")
                return []

            prefix = f"{self.prefix}{remote_path}" if remote_path else self.prefix
            files = []

            paginator = self.s3_client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                if "Contents" in page:
                    for obj in page["Contents"]:
                        key = obj["Key"]
                        # Remove prefix
                        relative_key = key.replace(self.prefix, "", 1)
                        files.append(relative_key)

            return files

        except Exception as e:
            logger.error(f"Error listing S3 files: {e}")
            return []

    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists in S3"""
        try:
            if not self.s3_client:
                return False

            key = f"{self.prefix}{remote_path}"
            self.s3_client.head_object(Bucket=self.bucket, Key=key)
            return True

        except Exception:
            return False

    def get_file_info(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """Get file information from S3"""
        try:
            if not self.s3_client:
                return None

            key = f"{self.prefix}{remote_path}"
            response = self.s3_client.head_object(Bucket=self.bucket, Key=key)

            return {
                "path": f"s3://{self.bucket}/{key}",
                "size": response["ContentLength"],
                "modified": response["LastModified"].timestamp(),
                "etag": response["ETag"],
                "storage_class": response.get("StorageClass", "STANDARD"),
            }

        except Exception as e:
            logger.error(f"Error getting S3 file info: {e}")
            return None


# Placeholder classes for other cloud providers
# These can be implemented similarly if needed

class AzureStorage(StorageBackend):
    """Azure Blob Storage backend (placeholder)"""

    def connect(self) -> bool:
        logger.warning("Azure Storage not yet implemented")
        return False

    def disconnect(self) -> None:
        pass

    def is_connected(self) -> bool:
        return False

    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        return False

    def download_file(self, remote_path: str, local_path: Path) -> bool:
        return False

    def delete_file(self, remote_path: str) -> bool:
        return False

    def list_files(self, remote_path: str = "") -> List[str]:
        return []

    def file_exists(self, remote_path: str) -> bool:
        return False

    def get_file_info(self, remote_path: str) -> Optional[Dict[str, Any]]:
        return None


class GoogleCloudStorage(StorageBackend):
    """Google Cloud Storage backend (placeholder)"""

    def connect(self) -> bool:
        logger.warning("Google Cloud Storage not yet implemented")
        return False

    def disconnect(self) -> None:
        pass

    def is_connected(self) -> bool:
        return False

    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        return False

    def download_file(self, remote_path: str, local_path: Path) -> bool:
        return False

    def delete_file(self, remote_path: str) -> bool:
        return False

    def list_files(self, remote_path: str = "") -> List[str]:
        return []

    def file_exists(self, remote_path: str) -> bool:
        return False

    def get_file_info(self, remote_path: str) -> Optional[Dict[str, Any]]:
        return None
