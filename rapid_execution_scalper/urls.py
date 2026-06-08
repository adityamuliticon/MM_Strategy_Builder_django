from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='res_index'),
    path('api/chat', views.chat, name='res_chat'),
    path('api/chat/stream', views.chat_stream, name='res_chat_stream'),
]
