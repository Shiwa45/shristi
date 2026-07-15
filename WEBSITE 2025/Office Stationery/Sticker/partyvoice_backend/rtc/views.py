"""
rtc/views.py — The token bridge.

Single responsibility: given an authenticated user and a room they're allowed
to enter, mint a short-lived, room-scoped ZEGOCLOUD Token04. The client calls
this right before initializing the Live Audio Room Kit, and again on
onTokenExpired to renew.
"""

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from rooms.models import Room, RoomBan
from .zego_token import generate_token04, build_room_privilege_payload


class RtcTokenView(APIView):
    """
    POST /api/rtc/token
    body: { "room_id": "<room_id>", "as_speaker": true|false }

    Returns a token scoped to that room. `as_speaker` controls publish
    privilege: speakers (host + seated users) may publish audio; pure
    audience get a login-only token (no publish), which prevents the
    'ghost microphone' problem.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "rtc_token"

    def post(self, request):
        room_id = (request.data.get("room_id") or "").strip()
        as_speaker = bool(request.data.get("as_speaker", False))

        if not room_id:
            return Response({"detail": "room_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not settings.ZEGO_APP_ID or len(settings.ZEGO_SERVER_SECRET) != 32:
            return Response(
                {"detail": "RTC is not configured on the server."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            room = Room.objects.get(room_id=room_id, status=Room.Status.LIVE)
        except Room.DoesNotExist:
            return Response({"detail": "Room not found or closed."}, status=status.HTTP_404_NOT_FOUND)

        # Bans block token issuance entirely.
        if RoomBan.objects.filter(room=room, user=request.user).exists():
            return Response({"detail": "You are banned from this room."}, status=status.HTTP_403_FORBIDDEN)

        # Only the owner/admins/seated users get publish; everyone else is audience.
        is_privileged = (room.owner_id == request.user.id) or room.admins.filter(id=request.user.id).exists()
        can_publish = as_speaker or is_privileged

        payload = build_room_privilege_payload(room.room_id, can_publish=can_publish)
        token = generate_token04(
            app_id=settings.ZEGO_APP_ID,
            user_id=request.user.zego_user_id,
            server_secret=settings.ZEGO_SERVER_SECRET,
            effective_time_seconds=settings.ZEGO_TOKEN_TTL_SECONDS,
            payload=payload,
        )

        return Response({
            "token": token,
            "app_id": settings.ZEGO_APP_ID,
            "user_id": request.user.zego_user_id,
            "room_id": room.room_id,
            "can_publish": can_publish,
            "expires_in": settings.ZEGO_TOKEN_TTL_SECONDS,
        })
