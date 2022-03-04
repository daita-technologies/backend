


# Set up
- install git
    https://www.atlassian.com/git/tutorials/install-git

- active ssh git key
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/link/to/private/key
    ssh -T git@github.com
    https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent

- create python virtual env
    python3 -m venv <name>

- activate env
    source <path/to/env>/bin/activate   (for Linux)
    <path/to/env>/Scripts/activate      (for Windows)

- install requirements
    pip install -r requirements.txt

- set up aws credential
    aws configure

- install and start redis
    https://www.codexpedia.com/devops/install-redis-on-amazon-aws-ec2-instance/

# Run
  - celery -A app_download.celery worker --loglevel=INFO -c 3
  - gunicorn -b 0.0.0.0:8000 app_download:app

