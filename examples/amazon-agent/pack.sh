find . | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf
zip -r package.zip app Dockerfile requirements.txt requirements.base.txt system_prompt.txt server.py scripts