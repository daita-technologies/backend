
# Install guide
- install python 3.7
- pip install virtualenv
- cd core_service
- virtualenv core_env
- activate env
- pip install -r requirements.txt
- set update default value for credential of user

For the first time init with admin_user:
- init sam
    https://medium.com/@edjgeek/meet-aws-sam-cli-sam-init-bab68b4cc0d4
    sam init -n daita-core-service-app -r python3.8