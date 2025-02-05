IF NOT EXIST venv (
    python -m venv venv
)
CALL ./venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
PAUSE