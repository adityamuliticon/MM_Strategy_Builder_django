from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_page, name='login'),
    path('auth/login/', views.auth_login, name='auth_login'),
    path('auth/logout/', views.auth_logout, name='auth_logout'),
    path('admin-login/', views.admin_login_page, name='admin_login'),
    path('admin-auth/', views.admin_auth_login, name='admin_auth_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('api/history/', views.history_api, name='history_api'),
]
