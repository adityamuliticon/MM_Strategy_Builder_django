from django.urls import path, include

urlpatterns = [
    path('', include('Unified_Strategy_Builder.urls')),
    path('indicator/', include('indicator_engine.urls')),
    path('bridge/', include('inbound_signal_bridge.urls')),
    path('scalper/', include('rapid_execution_scalper.urls')),
    path('hedger/', include('multi_leg_hedger.urls')),
    path('logs/', include('chat_logs.urls')),
]
