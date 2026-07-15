from django.urls import re_path

from games.consumers import GameConsumer

websocket_urlpatterns = [
    re_path(r"ws/game/(?P<session_id>[0-9]+)/$", GameConsumer.as_asgi()),
]
