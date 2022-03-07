#./__init__.py
from __future__ import absolute_import, unicode_literals
from AI_service.worker import app as celery_app 
__all__ = ['celery_app']
