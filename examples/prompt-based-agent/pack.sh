find . | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf
zip -r package.zip app Dockerfile requirements.txt system_prompt.txt server.py greeting.txt -x "*.DS_Store"