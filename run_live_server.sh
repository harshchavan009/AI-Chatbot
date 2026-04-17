#!/bin/bash

# Live Development Server for AI Chatbot
# This script starts the FastAPI application with auto-reload.

PORT=8000

echo "Starting Live Server on http://0.0.0.0:$PORT..."
echo "Press CTRL+C to stop the server."

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null
then
    echo "uvicorn could not be found, attempting to run with python3 -m uvicorn..."
    python3 -m uvicorn app.main:app --reload --port $PORT --host 0.0.0.0
else
    uvicorn app.main:app --reload --port $PORT --host 0.0.0.0
fi
