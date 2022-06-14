cd AI_service
celery -A AI_service.worker worker -l INFO -Q test & 
python manage.py runserver 0.0.0.0:443
