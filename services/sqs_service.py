import json
import boto3
from config import settings

# Initialize SQS client
sqs_client = boto3.client(
    "sqs",
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region
)

def send_message_to_queue(message_body: dict):
    """
    Sends a JSON message to the configured AWS SQS queue.
    """
    if not settings.sqs_queue_url:
        print("⚠️ Warning: SQS Queue URL is not set. Skipping message send.")
        return None

    try:
        response = sqs_client.send_message(
            QueueUrl=settings.sqs_queue_url,
            MessageBody=json.dumps(message_body)
        )
        return response.get("MessageId")
    except Exception as e:
        print(f"❌ Error sending message to SQS: {e}")
        raise e

def receive_messages_from_queue(max_messages: int = 1, wait_time_seconds: int = 10):
    """
    Polls the SQS queue for messages.
    Uses Long Polling (wait_time_seconds) to reduce empty API requests.
    """
    if not settings.sqs_queue_url:
        return []

    try:
        response = sqs_client.receive_message(
            QueueUrl=settings.sqs_queue_url,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=wait_time_seconds,
            VisibilityTimeout=1200 # Hide message for 20 minutes while we process it
        )
        return response.get("Messages", [])
    except Exception as e:
        print(f"❌ Error receiving messages from SQS: {e}")
        return []

def delete_message_from_queue(receipt_handle: str):
    """
    Deletes a message from the SQS queue after successful processing
    so another worker doesn't pick it up.
    """
    if not settings.sqs_queue_url:
        return

    try:
        sqs_client.delete_message(
            QueueUrl=settings.sqs_queue_url,
            ReceiptHandle=receipt_handle
        )
    except Exception as e:
        print(f"❌ Error deleting message from SQS: {e}")
