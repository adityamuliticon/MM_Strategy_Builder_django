from django.urls import path, re_path, include
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('', include('Unified_Strategy_Builder.urls')),
    path('indicator/', include('indicator_engine.urls')),
    path('bridge/', include('inbound_signal_bridge.urls')),
    path('scalper/', include('rapid_execution_scalper.urls')),
    path('hedger/', include('multi_leg_hedger.urls')),
    path('logs/', include('chat_logs.urls')),
    re_path(r'^static/(?P<path>.+)$', serve, {'document_root': settings.BASE_DIR / 'static'}),
]
