from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/chat', views.chat, name='chat'),
    path('api/chat/stream', views.chat_stream, name='chat_stream'),
    path('api/strategy-counts/', views.strategy_counts_view, name='strategy_counts'),
    path('api/balance/', views.balance_view, name='balance'),
]
