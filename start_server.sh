#!/bin/sh

source venv/bin/activate
uvicorn --app-dir=src html2pdfserver:app --reload