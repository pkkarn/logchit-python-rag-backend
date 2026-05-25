import boto3
from config import settings

s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region
)

def upload_pdf_to_s3(file_obj, filename: str):
    """
    Uploads a PDF to S3 and returns the S3 key.
    """
    try:
        bucket= settings.aws_bucket_name
        s3_client.upload_fileobj(
           Fileobj=file_obj,
           Bucket=bucket, 
           Key=filename,
           ExtraArgs={
            "ContentType": "application/pdf"
           }
        )
        s3_url = f"https://{bucket}.s3.{settings.aws_region}.amazonaws.com/{filename}"
        return s3_url
    except Exception as e:
        print(f"❌ Error uploading to S3: {e}")
        raise e

def download_pdf_from_s3(s3_url: str) -> bytes:
    """
    Downloads a file securely from S3 using boto3 authentication.
    Extracts the filename key from the S3 URL.
    """
    try:
        filename = s3_url.split("/")[-1]
        bucket = settings.aws_bucket_name
        response = s3_client.get_object(Bucket=bucket, Key=filename)
        return response['Body'].read()
    except Exception as e:
        print(f"❌ Error downloading from S3: {e}")
        raise e

def delete_pdf_from_s3(s3_url: str):
    """
    Deletes a file from the S3 bucket.
    Extracts the filename key from the S3 URL.
    """
    try:
        filename = s3_url.split("/")[-1]
        bucket = settings.aws_bucket_name
        s3_client.delete_object(Bucket=bucket, Key=filename)
        print(f"✅ Successfully deleted {filename} from S3.")
    except Exception as e:
        print(f"❌ Error deleting from S3: {e}")
        raise e