import redis
import os
import logging
import json
import datetime as dt
import logging.handlers as Handlers
import boto3

EXPIRED = 5 * 60
loggingDir = "/home/ec2-user/ec2_job"
os.makedirs(loggingDir, exist_ok=True)


def stop_ec2(ec2_id):
    client = boto3.client("lambda")
    try:
        response = client.invoke(
            FunctionName="staging-balancer-asy-stop",
            InvocationType="RequestResponse",
            Payload=json.dumps({"ec2_id": ec2_id}),
        )
        log.info(
            "[INFO] info request stop ec2: {}".format(
                json.loads(response["Payload"].read())
            )
        )
    except Exception as e:
        log.error("[ERROR] error request stop ec2: {}".format(e))


def setupLogger(name, level=logging.DEBUG):
    def filer(self):
        now = dt.datetime.now()
        return os.path.join(loggingDir, name + "_" + now.strftime("%Y-%m-%d") + ".log")

    formatter = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s - %(message)s")
    logger = logging.getLogger(name)
    logger.setLevel(level=level)
    logHandler = Handlers.TimedRotatingFileHandler(
        filename=os.path.join(loggingDir, name + ".log"),
        when="S",
        interval=86400,
        backupCount=1,
    )
    logHandler.rotation_filename = filer
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    logger.addHandler(logHandler)


def event_handler(msg):
    try:
        key = msg["data"].decode("utf-8")
        if "instanceKey" in key:
            log.info("[DEBUG] event_handler: {}".format(key))
            key = key.replace("instanceKey:", "")
            arr = [json.loads(conn.lindex(key, i)) for i in range(0, conn.llen(key))]
            if not len(arr):
                log.info("[INFO] info ec2 {}: task_Done".format(str(key)))
                stop_ec2(key)
                conn.delete(key)
            else:
                log.info("[INFO] info ec2 {}: add more expried time".format(str(key)))
                conn.set("instanceKey:" + key, "EX", EXPIRED)
    except Exception as e:
        print(e)
        log.error("[ERROR] {}".format(e))
        pass


setupLogger("job_ec2")
log = logging.getLogger("job_ec2")

conn = redis.Redis(host="localhost", port=6379, db=7)
pubsub = conn.pubsub()
conn.config_set("notify-keyspace-events", "Ex")
pubsub.psubscribe(**{"__keyevent@0__:expired": event_handler})
pubsub.run_in_thread(sleep_time=0.01)
print("Running : worker redis subscriber ...")
