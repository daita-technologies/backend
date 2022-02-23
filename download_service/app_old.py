from flask import Flask, jsonify
from flask import request
from itsdangerous import exc
from flask_cors import CORS, cross_origin

import download_task 
from task_worker import make_celery
import time

app = Flask(__name__)
app.config.from_object('settings')
celery = make_celery(app)

cors = CORS(app, resources={r"/*": {"origins": "*"}})
STATUS_FINISH = "FINISH"
STATUS_ERROR = "ERROR"


@celery.task(name="task_download")
def task_download(data):
    try:
        task_id = data["task_id"]
        identity_id = data["identity_id"]
        url, s3_key  = download_task.download(data)
        download_task.upload_progress_db(STATUS_FINISH, identity_id, task_id, url, s3_key)    
        print(url, s3_key)
        return "success"
    except Exception as e:
        print(e)
        url= None
        s3_key = None
        download_task.upload_progress_db(STATUS_ERROR, identity_id, task_id, url, s3_key)
        return "Error"

@app.route("/download", methods=['POST'])
def download():
    try:
        data = request.get_json()    
        print(data)             
        task = task_download.delay(data)
        print(task)
        return jsonify({
            "status": "OK"
        })
    
    except Exception as e:
        print(e)
        return "Error"   
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)