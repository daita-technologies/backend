celery -A AI_service.worker worker -l INFO -E -Q low   --pool=gevent --concurrency=100 -n worker1@0.0.0.0 &
celery -A AI_service.worker worker -l INFO -E -Q high  --concurrency=1 -n worker2@0.0.0.0 &
celery -A AI_service.worker worker -l INFO -E -Q request_ai   --pool=gevent  --concurrency=100 -n worker3@0.0.0.0 &
celery -A AI_service.worker worker -l INFO -E -Q request_ai   --pool=gevent  --concurrency=100 -n worker4@0.0.0.0 &
celery -A AI_service.worker worker -l INFO -E -Q download_image   --pool=gevent  --concurrency=100 -n worker5@0.0.0.0 &
celery -A AI_service.worker worker -l INFO -E -Q download_image   --pool=gevent  --concurrency=100 -n worker6@0.0.0.0 



