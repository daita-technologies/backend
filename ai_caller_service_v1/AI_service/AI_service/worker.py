from celery import Celery
from celery import shared_task
import os
import time

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "AI_service.settings"
)  # DON'T FORGET TO CHANGE THIS ACCORDINGLY
app = Celery(
    "AI_service", backend="redis://127.0.0.1:6379/2", broker="redis://127.0.0.1:6379/3"
)
app.config_from_object("django.conf:settings", namespace="CELERY")
