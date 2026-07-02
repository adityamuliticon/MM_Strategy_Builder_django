from django.http import JsonResponse

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
            from services.session_context import set_user_token, set_user_id
            set_user_id(user_id)
            token_record = UserBearerToken.objects.filter(user_id=user_id).first()
            if token_record:
                set_user_token(token_record.token)
        except Exception:
            pass

        request.app_user_id = user_id
        return self.get_response(request)
