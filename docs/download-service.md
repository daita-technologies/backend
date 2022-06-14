## Setup

- Installing Git: https://www.atlassian.com/git/tutorials/install-git

- Generating a new SSH key and adding it to the ssh-agent (see [here](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)):
    ```bash
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/link/to/private/key
    ssh -T git@github.com
    ```

- Creating Python virtual env:
    ```bash
    python3 -m venv <name>
    ```

- Activating virtual env:
    ```bash
    source <path/to/env>/bin/activate   (for Linux)
    <path/to/env>/Scripts/activate      (for Windows)
    ```

- Installing requirements
    ```bash
    pip install -r requirements.txt
    ```

- Seting up AWS credentials:
    ```bash
    aws configure
    ```

- Installing and starting Redis: https://www.codexpedia.com/devops/install-redis-on-amazon-aws-ec2-instance

## Run
```bash
celery -A app_download.celery worker --loglevel=INFO -c 3
gunicorn -b 0.0.0.0:8000 app_download:app
```
