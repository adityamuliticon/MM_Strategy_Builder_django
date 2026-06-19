from django.shortcuts import redirect
from django.http import JsonResponse

_EXCLUDED_PATHS = frozenset({
    '/login/',
    '/auth/login/',
    '/auth/logout/',
    '/admin-login/',
    '/admin-auth/',
    '/admin-logout/',
})


class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Static files and auth routes bypass auth check
        if path.startswith('/static/') or path in _EXCLUDED_PATHS:
            return self.get_response(request)

        # Admin panel has its own session check in the view
        if path.startswith('/admin-panel/') or path.startswith('/admin-'):
            return self.get_response(request)

        user_id = request.session.get('user_id')
        if not user_id:
            if path.startswith('/api/'):
                return JsonResponse(
                    {'error': 'Not authenticated', 'redirect': '/login/'},
                    status=401,
                )
            return redirect('/login/')

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
