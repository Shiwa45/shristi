"""rooms/serializers.py"""

from rest_framework import serializers

from .models import Room, SeatState


class SeatStateSerializer(serializers.ModelSerializer):
    occupant_name = serializers.SerializerMethodField()
    occupant_avatar = serializers.SerializerMethodField()
    occupant_id = serializers.SerializerMethodField()

    class Meta:
        model = SeatState
        fields = ["index", "muted", "locked", "occupant_id", "occupant_name", "occupant_avatar"]

    def get_occupant_id(self, obj):
        return obj.occupant.public_id.hex if obj.occupant_id else None

    def get_occupant_name(self, obj):
        if not obj.occupant_id:
            return None
        prof = getattr(obj.occupant, "profile", None)
        return prof.display_name if prof else obj.occupant.username

    def get_occupant_avatar(self, obj):
        if not obj.occupant_id:
            return None
        prof = getattr(obj.occupant, "profile", None)
        return prof.avatar_url if prof else ""


class RoomListSerializer(serializers.ModelSerializer):
    """Compact shape for the discovery list."""
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = [
            "room_id", "title", "category", "type", "room_type", "theme", "cover_url",
            "occupant_count", "seat_count", "is_locked", "owner_name",
        ]

    def get_owner_name(self, obj):
        prof = getattr(obj.owner, "profile", None)
        return prof.display_name if prof else obj.owner.username


class RoomDetailSerializer(RoomListSerializer):
    seats = SeatStateSerializer(many=True, read_only=True)
    is_owner = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    template = serializers.SerializerMethodField()
    theme_assets = serializers.SerializerMethodField()

    class Meta(RoomListSerializer.Meta):
        fields = RoomListSerializer.Meta.fields + [
            "status", "seats", "is_owner", "is_admin", "template", "theme_assets",
        ]

    def get_is_owner(self, obj):
        u = self.context["request"].user
        return obj.owner_id == u.id

    def get_is_admin(self, obj):
        u = self.context["request"].user
        return obj.admins.filter(id=u.id).exists()

    def get_template(self, obj):
        from .room_types import room_type_template
        t = room_type_template(obj.room_type)
        return {
            "label": t["label"],
            "seat_rows": t["seat_rows"],
            "special_seats": t["special_seats"],
        }

    def get_theme_assets(self, obj):
        from .room_types import RoomTheme, room_type_template
        key = obj.theme or room_type_template(obj.room_type)["default_theme"]
        theme = RoomTheme.objects.filter(key=key, is_active=True).first()
        return theme.assets if theme else {}


class RoomCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Room
        fields = ["title", "type", "room_type", "category", "theme", "cover_url", "seat_count", "password"]
        extra_kwargs = {"seat_count": {"required": False, "min_value": 1, "max_value": 20}}

    def validate(self, attrs):
        if attrs.get("type") == Room.Type.PRIVATE and not attrs.get("password"):
            raise serializers.ValidationError("Private rooms require a password.")
        return attrs

    def create(self, validated):
        from .room_types import room_type_template, seat_count_for_type
        password = validated.pop("password", "")
        room_type = validated.get("room_type", Room.RoomType.STANDARD)
        # seat count + default theme come from the room-type template
        validated["seat_count"] = seat_count_for_type(room_type)
        if not validated.get("theme"):
            validated["theme"] = room_type_template(room_type)["default_theme"]
        room = Room(owner=self.context["request"].user, **validated)
        room.set_password(password)
        room.save()
        # pre-create seat rows (index 0 = host/first special seat)
        SeatState.objects.bulk_create(
            [SeatState(room=room, index=i) for i in range(room.seat_count + 1)]
        )
        return room
