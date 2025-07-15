rm package.zip
zip -r package.zip src Dockerfile package.json tsconfig.json greeting.txt -x "*.DS_Store"