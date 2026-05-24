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