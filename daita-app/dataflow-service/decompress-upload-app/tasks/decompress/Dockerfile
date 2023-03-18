FROM python:3.11-bullseye

RUN apt-get update
RUN apt-get install -y \
    unzip \
    curl

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install

WORKDIR /app
ADD ./requirements.txt .
RUN pip install -r requirements.txt
ADD . .

CMD ["./cmd.sh"]
