FROM python:3.8-bullseye

WORKDIR /app
ADD ./requirements.txt .
RUN pip install -r requirements.txt
ADD . .

CMD ["./cmd.sh"]
