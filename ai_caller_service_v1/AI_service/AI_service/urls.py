"""AI_service URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path
from rest_framework import routers
from app.views import *

# router = routers.SimpleRouter()
# router.register(r'posts',PostDetailUpdateApiView,basename='Posts')
# router.register(r'posts',PostListCreateAPIView,basename='Posts')
urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"^v1/api/request_ai", AI_service_request),
    url(r"^v1/api/check_healthy", AI_service_check_healthy),
]
