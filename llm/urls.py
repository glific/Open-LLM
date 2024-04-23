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
"""

from django.contrib import admin
from django.urls import path

from llm.api import (
    create_chat,
    set_system_prompt,
    FileUploadView,
    set_evaluator_prompt,
    set_examples_text,
    set_openai_key,
    create_knowledge_category,
    get_knowledge_categories,
    delete_knowledge_category,
    get_documents,
    delete_document,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/chat", create_chat, name="create_chat"),
    path("api/upload", FileUploadView.as_view(), name="file_upload"),
    path("api/system_prompt", set_system_prompt, name="set_system_prompt"),
    path("api/evaluator_prompt", set_evaluator_prompt, name="set_evaluator_prompt"),
    path("api/examples_text", set_examples_text, name="set_examples_text"),
    path("api/openai_key", set_openai_key, name="set_openai_key"),
    path(
        "api/knowledge/category",
        create_knowledge_category,
        name="create_knowledge_category",
    ),
    path(
        "api/knowledge/category/get",
        get_knowledge_categories,
        name="get_knowledge_categories",
    ),
    path(
        "api/knowledge/category/<str:category_uuid>",
        delete_knowledge_category,
        name="delete_knowledge_category",
    ),
    path(
        "api/files",
        get_documents,
        name="get_documents",
    ),
    path(
        "api/files/<str:file_uuid>",
        delete_document,
        name="delete_document",
    ),
]
