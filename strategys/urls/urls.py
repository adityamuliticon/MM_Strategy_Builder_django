from django.urls import path
from strategys.views.views import (
    usb_chat, usb_chat_stream, strategy_counts_view, balance_view,
    mlh_chat, mlh_chat_stream,
    res_chat, res_chat_stream,
    isb_chat, isb_chat_stream,
    ise_chat, ise_chat_stream,
)

# USB (root)
usb_urlpatterns = [
    path('api/chat', usb_chat, name='chat'),
    path('api/chat/stream', usb_chat_stream, name='chat_stream'),
    path('api/strategy-counts/', strategy_counts_view, name='strategy_counts'),
    path('api/balance/', balance_view, name='balance'),
]

# MLH — /hedger/
mlh_urlpatterns = [
    path('api/chat', mlh_chat, name='mlh_chat'),
    path('api/chat/stream', mlh_chat_stream, name='mlh_chat_stream'),
]

# RES — /scalper/
res_urlpatterns = [
    path('api/chat', res_chat, name='res_chat'),
    path('api/chat/stream', res_chat_stream, name='res_chat_stream'),
]

# ISB — /bridge/
isb_urlpatterns = [
    path('api/chat', isb_chat, name='isb_chat'),
    path('api/chat/stream', isb_chat_stream, name='isb_chat_stream'),
]

# ISE — /indicator/
ise_urlpatterns = [
    path('api/chat', ise_chat, name='ise_chat'),
    path('api/chat/stream', ise_chat_stream, name='ise_chat_stream'),
]
