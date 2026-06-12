from django.urls import path
from . import views

urlpatterns = [
    path('', views.logs_index, name='logs_index'),
    path('api/', views.logs_api, name='logs_api'),
    path('api-calls/', views.api_logs_index, name='api_logs_index'),
    path('api-calls/api/', views.api_logs_api, name='api_logs_api'),
]
