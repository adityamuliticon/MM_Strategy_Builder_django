from django.http import JsonResponse
from services.session_context import set_user_token, set_user_id

_EXCLUDED_PATHS = frozenset({
    '/auth/login/',
    '/auth/logout/',
    '/docs/',
    '/openapi.json',
})


class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Reset thread-locals at the start of every request so a worker thread
        # that previously handled User A cannot leak A's token into User B's request.
        set_user_id(None)
        set_user_token('')

        path = request.path

        if path in _EXCLUDED_PATHS:
            return self.get_response(request)

        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)

        # Set per-user Market Maya token in thread-local so all downstream
        # API calls use this user's JWT without signature changes.
        try:
            from users.models import UserBearerToken
            set_user_id(user_id)
            token_record = UserBearerToken.objects.filter(user_id=user_id).first()
            if token_record:
                set_user_token(token_record.token)
        except Exception:
            pass

        request.app_user_id = user_id
        try:
            return self.get_response(request)
        finally:
            # Clear thread-locals after the request completes (belt-and-suspenders).
            set_user_id(None)
            set_user_token('')
