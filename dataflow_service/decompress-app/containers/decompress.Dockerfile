FROM ubuntu:20.04

RUN apt-get update
RUN apt-get install -y \
    unzip \
    curl
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install