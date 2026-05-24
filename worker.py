import json
import time
from config import settings
from services.sqs_service import receive_messages_from_queue, delete_message_from_queue
from services.ingestion_service import process_document_background
from database.postgres import get_db_connection, update_document_status,get_document_status
from services.s3_service import download_pdf_from_s3

def start_worker():
    print("🚀 SQS Worker started. Polling for messages...")
    while True:
        try:
            # Uses Long Polling to wait up to 10 seconds for a message
            messages = receive_messages_from_queue(max_messages=1, wait_time_seconds=10)
            if not messages:
                continue

            for message in messages:
                receipt_handle = message['ReceiptHandle']
                body = json.loads(message['Body'])
                
                document_id = body.get("document_id")
                user_id = body.get("user_id")
                s3_url = body.get("s3_url")

                print(f"📥 Received job for document: {document_id}")
                
                try:
                    # --- IDEMPOTENCY CHECK ---
                    # Check if another worker (or a previous attempt) already finished this job
                    conn = get_db_connection()
                    try:
                        current_status = get_document_status(conn, document_id)
                    finally:
                        conn.close()

                    if current_status == 'COMPLETED':
                        print(f"⏭️ Document {document_id} is already COMPLETED. Skipping duplicate message.")
                        delete_message_from_queue(receipt_handle)
                        continue
                    # -------------------------

                    # 1. Download the PDF from S3
                    print("⬇️ Downloading file from S3...")
                    file_bytes = download_pdf_from_s3(s3_url)
                    
                    # 2. Process document (chunk, embed batch, pinecone upsert batch)
                    print("⚙️ Processing document chunks and embeddings...")
                    process_document_background(file_bytes, document_id, user_id)
                    
                    # 3. Update Status to COMPLETED
                    conn = get_db_connection()
                    try:
                        update_document_status(conn, document_id, 'COMPLETED')
                        conn.commit()
                    finally:
                        conn.close()
                    
                    # 4. Delete message from SQS
                    delete_message_from_queue(receipt_handle)
                    print(f"✅ Successfully processed document: {document_id}")

                except Exception as e:
                    print(f"❌ Error processing document {document_id}: {e}")
                    # Update status to FAILED
                    conn = get_db_connection()
                    try:
                        update_document_status(conn, document_id, 'FAILED')
                        conn.commit()
                    finally:
                        conn.close()

        except Exception as e:
            print(f"❌ Worker loop error: {e}")
            time.sleep(5) # Prevent tight loop if SQS connection fails

if __name__ == "__main__":
    start_worker()
