virtualenv -p python env
source env/bin/activate 
pip install aws_encryption_sdk
zip -g my-deployment-package.zip lambda_function.py