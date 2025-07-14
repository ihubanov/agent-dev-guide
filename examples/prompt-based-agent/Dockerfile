from python:3.12-slim

copy requirements.txt requirements.txt
run pip install -r requirements.txt
run playwright install

workdir workspace
copy server.py server.py
copy app app
copy system_prompt.txt system_prompt.txt

cmd ["python", "server.py"]