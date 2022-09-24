FROM python:3.8.13-slim

# Install necessary build tools
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends build-essential ffmpeg libsm6 libxext6

# Change default directory
WORKDIR /app

# Install dependencies
COPY requirements-cpu.txt .
RUN pip install -r requirements-cpu.txt --find-links=https://download.pytorch.org/whl/torch_stable.html --no-cache-dir


COPY task.py /tmp
CMD python /tmp/task.py