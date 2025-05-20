from typing import Optional
import os
import time
import boto3
import logging
from typing import Dict, Any
from botocore.exceptions import ClientError

from app.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CloudflareR2Uploader:
    """
    Class for uploading files to Cloudflare R2 storage
    """

    def __init__(self):
        """
        Initialize the R2 client using credentials from settings
        """
        self.endpoint_url = settings.R2_ENDPOINT_URL
        self.access_key_id = settings.R2_ACCESS_KEY_ID
        self.secret_access_key = settings.R2_SECRET_ACCESS_KEY
        self.bucket_name = settings.R2_BUCKET_NAME
        self.path_prefix = settings.R2_PATH_PREFIX
        self.custom_url = settings.R2_URL  # Custom domain for R2 public access

        # Validate required settings
        if not all([self.endpoint_url, self.access_key_id, self.secret_access_key]):
            logger.warning(
                "Missing R2 credentials. Upload functionality will not work."
            )

        # Initialize S3 client for R2
        self.client = boto3.client(
            service_name="s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name="auto",  # Cloudflare R2 uses 'auto' or specific regions like 'wnam', 'enam', etc.
        )

    def upload_file(
        self,
        file_path: str,
        content_type: str = "application/json",
        custom_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload a file to Cloudflare R2

        Args:
            file_path (str): Path to the file to upload
            content_type (str): Content type of the file
            custom_key (str, optional): Custom object key to use instead of generating one

        Returns:
            Dict[str, Any]: Upload result with URL
        """
        try:
            # Generate object key with timestamp or use custom key if provided
            timestamp = int(time.time())
            filename = os.path.basename(file_path)

            if custom_key:
                object_key = custom_key
                logger.info(f"Using custom object key: {object_key}")
            else:
                # Default key for Lottie JSON files
                extension = os.path.splitext(filename)[1] or ".json"
                object_key = f"{self.path_prefix}/{timestamp}{extension}"
                logger.info(f"Generated object key: {object_key}")

            # Upload file to R2
            self.client.upload_file(
                Filename=file_path,
                Bucket=self.bucket_name,
                Key=object_key,
                ExtraArgs={
                    "ContentType": content_type,
                    "ACL": "public-read",  # Explicitly set ACL to ensure accessibility
                },
            )

            # Use custom domain URL if available, otherwise fall back to pre-signed URL
            if self.custom_url:
                # Use the custom domain URL for public access
                url = f"{self.custom_url}/{object_key}"
                logger.info(f"Generated custom domain URL: {url}")
            else:
                # Fall back to pre-signed URL if custom domain is not configured
                try:
                    # Generate a pre-signed URL that works with Cloudflare R2
                    url = self.client.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": self.bucket_name, "Key": object_key},
                        ExpiresIn=604800,  # URL valid for 1 week (in seconds) - maximum allowed by Cloudflare R2
                    )
                    logger.info(
                        "Generated pre-signed URL with 1 week expiration (maximum allowed)"
                    )
                except Exception as e:
                    logger.warning(f"Could not generate pre-signed URL: {str(e)}")
                    # Fall back to using a public download URL format for Cloudflare R2
                    # This requires that you've set up a public access policy in Cloudflare R2 dashboard
                    account_id = self.endpoint_url.split(".")[0].replace("https://", "")
                    url = f"https://{account_id}.r2.dev/{self.bucket_name}/{object_key}"
                    logger.info(
                        f"Using Cloudflare R2 public download URL format: {url}"
                    )

            logger.info(f"Successfully uploaded file to {url}")
            return {
                "success": True,
                "url": url,
                "object_key": object_key,
                "bucket": self.bucket_name,
            }

        except ClientError as e:
            logger.error(f"Error uploading to R2: {str(e)}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error uploading to R2: {str(e)}")
            return {"success": False, "error": str(e)}

    def check_bucket_exists(self) -> bool:
        """
        Check if the configured bucket exists

        Returns:
            bool: True if bucket exists, False otherwise
        """
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError as e:
            logger.error(f"Error checking bucket: {str(e)}")
            return False

    def create_bucket_if_not_exists(self) -> bool:
        """
        Create the bucket if it doesn't exist

        Returns:
            bool: True if bucket exists or was created, False on error
        """
        try:
            if not self.check_bucket_exists():
                self.client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            return True
        except ClientError as e:
            logger.error(f"Error creating bucket: {str(e)}")
            return False
