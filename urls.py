from django.urls import path, include
from django.http import JsonResponse
from services.request_queue import request_queue
from strategys.urls.urls import (
    usb_urlpatterns,
    ise_urlpatterns,
    isb_urlpatterns,
    res_urlpatterns,
    mlh_urlpatterns,
)
from api_docs import openapi_spec, redoc_view


def queue_stats(request):
    return JsonResponse(request_queue.stats)


urlpatterns = [
    # Docs (public — excluded from auth)
    path('docs/', redoc_view, name='redoc'),
    path('openapi.json', openapi_spec, name='openapi_spec'),

    path('api/queue-stats/', queue_stats, name='queue_stats'),
    path('', include('users.urls')),
    path('', include(usb_urlpatterns)),
    path('indicator/', include(ise_urlpatterns)),
    path('bridge/', include(isb_urlpatterns)),
    path('scalper/', include(res_urlpatterns)),
    path('hedger/', include(mlh_urlpatterns)),
    path('logs/', include('chat_logs.urls')),
]
