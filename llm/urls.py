"""
URL configuration for llm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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

    curl -X POST -H "Content-Type: multipart/form-data" -F "file=@llm/data/sources/ANXIETY.docx.pdf" http://localhost:8000/api/upload
"""
from django.contrib import admin
from django.urls import path

from llm.api import create_chat, create_embeddings, FileUploadView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/chat", create_chat, name="create_chat"),
    path("api/embeddings", create_embeddings, name="create_embeddings"),
    path("api/upload", FileUploadView.as_view(), name="file-upload")
]

