set SERVER_PORT=8000
set SERVER_IP=0.0.0.0

IF NOT EXIST venv (
    CALL ./install.bat
)

CALL ./venv/Scripts/activate
uvicorn --host %SERVER_IP% --port %SERVER_PORT% --app-dir=src pdf2htmlserver:app --reload
PAUSE