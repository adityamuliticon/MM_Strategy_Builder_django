from django.urls import path
from . import views

urlpatterns = [
    path('', views.logs_index, name='logs_index'),
    path('api/', views.logs_api, name='logs_api'),
]
