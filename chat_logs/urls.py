from django.urls import path
from . import views

urlpatterns = [
    path('api/', views.logs_api, name='logs_api'),
    path('api-calls/api/', views.api_logs_api, name='api_logs_api'),
]
