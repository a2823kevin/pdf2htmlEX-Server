#!/usr/bin/bash

source .env
source venv/bin/activate
uvicorn --host 0.0.0.0 --port $SERVER_PORT --app-dir=src pdf2htmlserver:app --reload