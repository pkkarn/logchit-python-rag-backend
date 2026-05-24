#!/bin/bash
# A convenient script to run both the FastAPI server and SQS Worker locally

# Trap CTRL+C (SIGINT) and kill all background processes started by this script
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

echo "🚀 Starting FastAPI Web Server (Port 8000)..."
./venv/bin/uvicorn main:app --reload &

echo "⚙️ Starting SQS Background Worker..."
./venv/bin/python worker.py &

# Wait for both background processes to finish (or until user hits CTRL+C)
wait
