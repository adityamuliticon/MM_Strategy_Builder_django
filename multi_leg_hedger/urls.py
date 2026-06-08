from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='mlh_index'),
    path('api/chat', views.chat, name='mlh_chat'),
    path('api/chat/stream', views.chat_stream, name='mlh_chat_stream'),
]
