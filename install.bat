docker pull pdf2htmlex/pdf2htmlex:0.18.8.rc2-master-20200820-ubuntu-20.04-x86_64

IF NOT EXIST venv (
    python -m venv venv
)
CALL ./venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
PAUSE