"""
rtc/ws_auth.py — Authenticate WebSocket connections with a JWT query param.

Channels doesn't run DRF auth, so we resolve the user from a ?token=<access_jwt>
on the ws:// URL before the consumer runs. The Flutter client appends its
SimpleJWT access token when opening the room socket.
"""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def _get_user(token_str):
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import TokenError
    from accounts.models import User
    if not token_str:
        return AnonymousUser()
    try:
        access = AccessToken(token_str)
        return User.objects.get(id=access["user_id"])
    except (TokenError, KeyError, User.DoesNotExist):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        token = (query.get("token") or [None])[0]
        scope["user"] = await _get_user(token)
        return await super().__call__(scope, receive, send)
