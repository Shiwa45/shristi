"""
rooms/profile_theme_views.py — Profile fetch + room theme store + admin actions.

  GET  /api/users/<public_id>           public profile (tapped in a room)
  GET  /api/room-themes                  theme catalog (+ owned flag)
  POST /api/room-themes/<key>/buy        purchase a theme (coins)
  POST /api/rooms/<room_id>/apply-theme  owner applies an owned theme
  POST /api/rooms/<room_id>/admins       owner adds/removes a room admin
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from economy.models import Currency, Transaction, Wallet
from economy.services import InsufficientFunds, debit
from .models import Room
from .room_types import RoomTheme, RoomThemeOwnership


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile(request, public_id):
    """Public profile shown when a user taps a seat/avatar in a room."""
    user = User.objects.filter(public_id=public_id).select_related("profile").first()
    if not user:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    prof = getattr(user, "profile", None)
    wallet = Wallet.objects.filter(user=user).first()
    # follow state of the viewer toward this user
    from social.feed import Relationship
    is_following = Relationship.objects.filter(
        user=request.user, target=user, type=Relationship.Type.FOLLOW).exists()
    return Response({
        "user_id": user.public_id.hex,
        "display_name": prof.display_name if prof else user.username,
        "avatar_url": prof.avatar_url if prof else "",
        "gender": prof.gender if prof else "u",
        "bio": prof.bio if prof else "",
        "level": prof.level if prof else 1,
        "wealth": wallet.lifetime_coins_spent if wallet else 0,
        "charm": wallet.lifetime_diamonds_earned if wallet else 0,
        "is_following": is_following,
        "is_self": user.id == request.user.id,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def room_themes(request):
    """Theme catalog with an `owned` flag for the viewer."""
    owned_keys = set(RoomThemeOwnership.objects.filter(
        user=request.user).values_list("theme__key", flat=True))
    themes = RoomTheme.objects.filter(is_active=True).order_by("sort_order", "coin_cost")
    return Response([{
        "key": t.key,
        "name": t.name,
        "coin_cost": t.coin_cost,
        "preview_url": t.preview_url,
        "assets": t.assets,
        "is_default": t.is_default,
        "owned": t.is_default or t.key in owned_keys,
    } for t in themes])


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def buy_theme(request, key):
    theme = RoomTheme.objects.filter(key=key, is_active=True).first()
    if not theme:
        return Response({"detail": "Theme not found."}, status=status.HTTP_404_NOT_FOUND)
    if theme.is_default or theme.coin_cost == 0:
        RoomThemeOwnership.objects.get_or_create(user=request.user, theme=theme)
        return Response({"ok": True, "owned": True})
    if RoomThemeOwnership.objects.filter(user=request.user, theme=theme).exists():
        return Response({"ok": True, "owned": True})
    try:
        debit(user_id=request.user.id, currency=Currency.COIN, amount=theme.coin_cost,
              txn_type=Transaction.Type.PURCHASE,
              idempotency_key=f"theme:{request.user.id}:{key}",
              initiator_id=request.user.id, system_sink=True,
              metadata={"reason": "room_theme", "theme": key})
    except InsufficientFunds:
        return Response({"detail": "Not enough coins."}, status=status.HTTP_402_PAYMENT_REQUIRED)
    RoomThemeOwnership.objects.create(user=request.user, theme=theme)
    return Response({"ok": True, "owned": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def apply_theme(request, room_id):
    room = Room.objects.filter(room_id=room_id).first()
    if not room:
        return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)
    if room.owner_id != request.user.id:
        return Response({"detail": "Only the owner can change the theme."},
                        status=status.HTTP_403_FORBIDDEN)
    key = request.data.get("theme")
    theme = RoomTheme.objects.filter(key=key, is_active=True).first()
    if not theme:
        return Response({"detail": "Theme not found."}, status=status.HTTP_404_NOT_FOUND)
    owns = theme.is_default or RoomThemeOwnership.objects.filter(
        user=request.user, theme=theme).exists()
    if not owns:
        return Response({"detail": "You don't own this theme."},
                        status=status.HTTP_403_FORBIDDEN)
    room.theme = key
    room.save(update_fields=["theme"])
    return Response({"ok": True, "theme": key, "assets": theme.assets})


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def room_admins(request, room_id):
    """Owner adds (POST) or removes (DELETE) a room admin by public_id."""
    room = Room.objects.filter(room_id=room_id).first()
    if not room:
        return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)
    if room.owner_id != request.user.id:
        return Response({"detail": "Only the owner can manage admins."},
                        status=status.HTTP_403_FORBIDDEN)
    target = User.objects.filter(public_id=request.data.get("user_id")).first()
    if not target:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "POST":
        room.admins.add(target)
    else:
        room.admins.remove(target)
    return Response({"ok": True})
