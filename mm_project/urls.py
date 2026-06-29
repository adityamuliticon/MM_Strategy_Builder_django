from django.urls import path, re_path, include
from django.conf import settings
from django.views.static import serve
from django.http import JsonResponse
from services.request_queue import request_queue
from strategys.urls.urls import (
    usb_urlpatterns,
    ise_urlpatterns,
    isb_urlpatterns,
    res_urlpatterns,
    mlh_urlpatterns,
)


def queue_stats(request):
    return JsonResponse(request_queue.stats)


urlpatterns = [
    path('api/queue-stats/', queue_stats, name='queue_stats'),
    path('', include('users.urls')),
    path('', include(usb_urlpatterns)),
    path('indicator/', include(ise_urlpatterns)),
    path('bridge/', include(isb_urlpatterns)),
    path('scalper/', include(res_urlpatterns)),
    path('hedger/', include(mlh_urlpatterns)),
    path('logs/', include('chat_logs.urls')),
    re_path(r'^static/(?P<path>.+)$', serve, {'document_root': settings.BASE_DIR / 'static'}),
]
