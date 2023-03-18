FROM python:3.11-bullseye

WORKDIR /app
ADD ./requirements.txt .
RUN pip install -r requirements.txt
ADD . .

CMD ["./cmd.sh"]
