from django.urls import path, include

urlpatterns = [
    path('', include('chat.urls')),
    path('indicator/', include('indicator_engine.urls')),
]
