from django.urls import path, include

urlpatterns = [
    path('', include('Unified_Strategy_Builder.urls')),
    path('indicator/', include('indicator_engine.urls')),
    path('bridge/', include('inbound_signal_bridge.urls')),
]
