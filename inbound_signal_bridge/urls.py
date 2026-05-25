from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='isb_index'),
    path('api/chat', views.chat, name='isb_chat'),
]
