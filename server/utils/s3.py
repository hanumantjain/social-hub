"""
AWS S3 utilities for file upload and management
"""
import boto3
from botocore.exceptions import ClientError
from logger import logger
import os
from typing import Optional
import uuid
from pathlib import Path

class S3Handler:
    """Handle S3 file operations"""
    
    def __init__(self):
        """Initialize S3 client with credentials from environment"""
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Check if we're in Lambda or local development
        is_lambda = os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None
        
        # In Lambda, ALWAYS use IAM role (never explicit credentials)
        if is_lambda:
            logger.info("Running in Lambda - using IAM role credentials")
            self.s3_client = boto3.client('s3', region_name=self.region)
        else:
            # Local development - use explicit credentials if provided
            aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            
            if aws_access_key and aws_secret_key:
                logger.info("Running locally - using explicit credentials")
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    region_name=self.region
                )
            else:
                logger.info("Running locally - using default AWS credentials (from ~/.aws/credentials)")
                self.s3_client = boto3.client('s3', region_name=self.region)
        
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.cloudfront_domain = os.getenv('CLOUDFRONT_DOMAIN')  # Optional
        
        if not self.bucket_name:
            logger.error("S3_BUCKET_NAME environment variable not set")
            raise ValueError("S3_BUCKET_NAME must be set in environment variables")
    
    def upload_file(
        self, 
        file_obj, 
        filename: str, 
        content_type: str = 'image/jpeg'
    ) -> Optional[str]:
        """
        Upload file to S3 and return the URL
        
        Args:
            file_obj: File object to upload
            filename: Original filename (extension will be preserved)
            content_type: MIME type of the file
            
        Returns:
            Public URL of uploaded file, or None if upload failed
        """
        try:
            # Generate unique filename
            file_extension = Path(filename).suffix.lower()
            unique_filename = f"posts/{uuid.uuid4()}{file_extension}"
            
            # Upload to S3
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                unique_filename,
                ExtraArgs={
                    'ContentType': content_type,
                    'CacheControl': 'max-age=31536000',  # Cache for 1 year
                }
            )
            
            # Generate URL
            if self.cloudfront_domain:
                # Use CloudFront URL if available (better performance)
                url = f"https://{self.cloudfront_domain}/{unique_filename}"
            else:
                # Use direct S3 URL with region
                url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{unique_filename}"
            
            logger.info(f"File uploaded to S3: {unique_filename} -> {url}")
            return url
            
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {str(e)}")
            return None
    
    def delete_file(self, file_url: str) -> bool:
        """
        Delete file from S3
        
        Args:
            file_url: Full URL of the file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Extract key from URL
            if self.cloudfront_domain and self.cloudfront_domain in file_url:
                # CloudFront URL
                key = file_url.split(self.cloudfront_domain + '/')[-1]
            else:
                # S3 URL
                key = file_url.split('.amazonaws.com/')[-1]
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            logger.info(f"File deleted from S3: {key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete from S3: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during S3 deletion: {str(e)}")
            return False
    
    def get_presigned_url(self, file_url: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for private files
        
        Args:
            file_url: Full URL of the file
            expiration: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Presigned URL or None if failed
        """
        try:
            # Extract key from URL
            key = file_url.split('.amazonaws.com/')[-1]
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expiration
            )
            
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            return None
    
    def generate_presigned_upload_url(self, filename: str, content_type: str, expires_in: int = 3600) -> dict:
        """
        Generate a pre-signed URL for direct upload to S3 from the browser
        
        Args:
            filename: Original filename
            content_type: MIME type of the file
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            dict with 'upload_url', 'key', and 'public_url'
        """
        try:
            # Generate unique filename
            file_extension = Path(filename).suffix.lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            key = f"posts/{unique_filename}"
            
            logger.info(f"Generating pre-signed URL for upload: {key}")
            
            # Generate pre-signed URL for PUT operation
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key,
                    'ContentType': content_type,
                },
                ExpiresIn=expires_in,
                HttpMethod='PUT'
            )
            
            # Generate the public URL (what the image URL will be after upload)
            if self.cloudfront_domain:
                public_url = f"https://{self.cloudfront_domain}/{key}"
            else:
                public_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
            
            logger.info(f"Generated pre-signed URL for: {key}")
            
            return {
                'upload_url': presigned_url,
                'key': key,
                'public_url': public_url
            }
            
        except ClientError as e:
            logger.error(f"Failed to generate pre-signed URL: {str(e)}")
            raise Exception(f"Failed to generate upload URL: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error generating pre-signed URL: {str(e)}")
            raise Exception(f"Failed to generate upload URL: {str(e)}")

# Create a singleton instance
s3_handler = S3Handler()

