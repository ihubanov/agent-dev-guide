rm package.zip
zip -r package.zip src scripts Dockerfile package.json tsconfig.json greeting.txt -x "*.DS_Store"