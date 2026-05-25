from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='ise_index'),
    path('api/chat', views.chat, name='ise_chat'),
]
