from django.urls import path
from . import views

urlpatterns = [
    path('auth/login/', views.auth_login, name='auth_login'),
    path('auth/logout/', views.auth_logout, name='auth_logout'),
    path('api/history/', views.history_api, name='history_api'),
]
