import redis
import os
import logging
import json
import datetime as dt
import logging.handlers as Handlers
import boto3

EXPIRED = 60 * 31 + 30
# loggingDir ='./ec2_job'
# os.makedirs(loggingDir,exist_ok=True)


def stop_ec2(ec2_id):
    client = boto3.client("lambda")
    print("[DEBUG] stop ec2: {}".format(ec2_id))
    # log.debug("[DEBUG] stop ec2: {}".format(ec2_id))
    try:
        response = client.invoke(
            FunctionName="staging-balancer-asy-stop",
            InvocationType="RequestResponse",
            Payload=json.dumps({"ec2_id": ec2_id}),
        )
        print(
            "[INFO] info request stop ec2: {}".format(
                json.loads(response["Payload"].read())
            )
        )
        # log.info("[INFO] info request stop ec2: {}".format(json.loads(response['Payload'].read())))
    except Exception as e:
        print("[ERROR] error request stop ec2: {}".format(e))
        # log.error("[ERROR] error request stop ec2: {}".format(e))


def event_handler(msg):
    try:
        key = msg["data"].decode("utf-8")
        if "instanceKey" in key:
            print(key)
            key = key.replace("instanceKey:", "")
            # arr = [json.loads(conn.lindex(key, i)) for i in range(0, conn.llen(key))]
            print("{} --- {}".format(key, conn.llen(key)))
            if not conn.llen(key):
                stop_ec2(key)
                conn.delete("instanceKey:" + key)
                conn.delete(key)
                print("delete completed {}".format(key))
            else:
                print("Expired continue: {}".format(key))
                conn.set("instanceKey:" + key, "EX", EXPIRED)
    except Exception as e:
        print(e)
        pass


conn = redis.Redis(host="localhost", port=6379, db=0)
pubsub = conn.pubsub()
conn.config_set("notify-keyspace-events", "Ex")
pubsub.psubscribe(**{"__keyevent@0__:expired": event_handler})
pubsub.run_in_thread(sleep_time=0.01)
print("Running : worker redis subscriber ...")
