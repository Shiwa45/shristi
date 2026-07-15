"""
rooms/views.py — Room lifecycle + discovery REST API.

Realtime seat changes happen over the WebSocket consumer; these endpoints
handle durable lifecycle (create/close/lock), discovery listing, and the
join handshake that authorizes a client before it requests an RTC token.
"""

from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Room, RoomBan
from .serializers import (
    RoomCreateSerializer,
    RoomDetailSerializer,
    RoomListSerializer,
)


class RoomViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    lookup_field = "room_id"

    def get_queryset(self):
        qs = Room.objects.filter(status=Room.Status.LIVE).select_related("owner", "owner__profile")
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        search = self.request.query_params.get("q")
        if search:
            qs = qs.filter(Q(title__icontains=search))
        # default discovery order: hottest rooms first
        return qs.order_by("-occupant_count", "-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return RoomCreateSerializer
        if self.action in ("retrieve",):
            return RoomDetailSerializer
        return RoomListSerializer

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        room = ser.save()
        return Response(RoomDetailSerializer(room, context={"request": request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def join(self, request, room_id=None):
        """
        Authorize entry. Validates ban + password, then tells the client to
        proceed to /api/rtc/token. Does NOT itself seat the user (seats are
        taken over the WebSocket once inside).
        """
        room = self.get_object()
        if RoomBan.objects.filter(room=room, user=request.user).exists():
            return Response({"detail": "You are banned from this room."}, status=status.HTTP_403_FORBIDDEN)

        if room.is_locked:
            supplied = request.data.get("password", "")
            if not room.check_password(supplied):
                return Response({"detail": "Incorrect room password."}, status=status.HTTP_403_FORBIDDEN)

        return Response({
            "ok": True,
            "room": RoomDetailSerializer(room, context={"request": request}).data,
            "next": "request an RTC token from /api/rtc/token",
        })

    @action(detail=True, methods=["post"])
    def lock(self, request, room_id=None):
        room = self.get_object()
        if room.owner_id != request.user.id:
            return Response({"detail": "Only the owner can lock the room."}, status=status.HTTP_403_FORBIDDEN)
        password = request.data.get("password", "")
        if password:
            room.type = Room.Type.PRIVATE
            room.set_password(password)
        else:
            room.type = Room.Type.PUBLIC
            room.password_hash = ""
        room.save(update_fields=["type", "password_hash"])
        return Response({"ok": True, "is_locked": room.is_locked})

    @action(detail=True, methods=["post"])
    def close(self, request, room_id=None):
        room = self.get_object()
        if room.owner_id != request.user.id and not request.user.is_staff:
            return Response({"detail": "Only the owner can close the room."}, status=status.HTTP_403_FORBIDDEN)
        room.status = Room.Status.CLOSED
        room.closed_at = timezone.now()
        room.save(update_fields=["status", "closed_at"])
        return Response({"ok": True})
