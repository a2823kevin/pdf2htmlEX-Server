#!/usr/bin/bash

sudo apt update
sudo apt install libmagic1

python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
