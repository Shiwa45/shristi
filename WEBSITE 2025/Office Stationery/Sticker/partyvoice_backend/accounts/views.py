"""
accounts/views.py — phone OTP auth + profile/avatar.

  POST /api/auth/phone/otp      request an OTP for a phone number
  POST /api/auth/phone/verify   verify OTP -> returns JWT access/refresh
  GET  /api/me                  current user's profile
  PATCH/api/me                  update display_name / bio
  POST /api/me/avatar           set avatar_url (or upload, see note)

OTP delivery: in production wire an SMS provider (Twilio/MSG91) in
`_send_sms`. For development, DEBUG returns the code in the response and also
accepts the universal dev code '000000' so you can sign in without SMS.
"""

import random

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Profile, User

OTP_TTL_SECONDS = 300
DEV_UNIVERSAL_CODE = "000000"


def _otp_key(phone: str) -> str:
    return f"otp:{phone}"


def _send_sms(phone: str, code: str):
    """Wire a real SMS provider here for production."""
    if settings.DEBUG:
        print(f"[DEV OTP] {phone} -> {code}")


@api_view(["POST"])
@permission_classes([AllowAny])
def request_otp(request):
    phone = (request.data.get("phone") or "").strip()
    if not phone or len(phone) < 6:
        return Response({"detail": "A valid phone number is required."},
                        status=status.HTTP_400_BAD_REQUEST)
    code = f"{random.randint(0, 999999):06d}"
    cache.set(_otp_key(phone), code, OTP_TTL_SECONDS)
    _send_sms(phone, code)
    payload = {"ok": True, "expires_in": OTP_TTL_SECONDS}
    if settings.DEBUG:
        payload["dev_code"] = code  # convenience in development only
    return Response(payload)


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):
    phone = (request.data.get("phone") or "").strip()
    otp = (request.data.get("otp") or "").strip()
    if not phone or not otp:
        return Response({"detail": "Phone and code are required."},
                        status=status.HTTP_400_BAD_REQUEST)

    expected = cache.get(_otp_key(phone))
    dev_ok = settings.DEBUG and otp == DEV_UNIVERSAL_CODE
    if not dev_ok and (expected is None or otp != expected):
        return Response({"detail": "Invalid or expired code."},
                        status=status.HTTP_401_UNAUTHORIZED)
    cache.delete(_otp_key(phone))

    user, created = User.objects.get_or_create(
        username=phone, defaults={"is_active": True})
    if created:
        Profile.objects.get_or_create(
            user=user, defaults={"display_name": f"User{user.id}"})

    refresh = RefreshToken.for_user(user)
    prof = getattr(user, "profile", None)
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "is_new": created,
        "user": {
            "user_id": user.public_id.hex,
            "display_name": prof.display_name if prof else user.username,
            "avatar_url": prof.avatar_url if prof else "",
        },
    })


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    prof, _ = Profile.objects.get_or_create(user=user)
    if request.method == "PATCH":
        if "display_name" in request.data:
            prof.display_name = request.data["display_name"][:40]
        if "bio" in request.data:
            prof.bio = request.data["bio"][:200]
        prof.save()
    return Response({
        "user_id": user.public_id.hex,
        "display_name": prof.display_name,
        "avatar_url": prof.avatar_url,
        "bio": prof.bio,
        "level": prof.level,
        "gender": prof.gender,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def set_avatar(request):
    """Set the avatar by URL.

    Two supported flows:
      1) Client uploads the image to object storage (S3/GCS/Cloudinary) and
         POSTs the resulting public URL here as {"avatar_url": "..."}.
      2) Direct multipart upload: if an image file is attached, it is saved to
         MEDIA and the served URL is stored. (Requires MEDIA_URL/ROOT + a
         storage backend configured; URL flow is recommended for production
         CDNs.)
    """
    prof, _ = Profile.objects.get_or_create(user=request.user)
    url = request.data.get("avatar_url")
    if url:
        prof.avatar_url = url[:200]
        prof.save(update_fields=["avatar_url"])
        return Response({"ok": True, "avatar_url": prof.avatar_url})

    upload = request.FILES.get("file")
    if upload:
        from django.core.files.storage import default_storage
        path = default_storage.save(
            f"avatars/{request.user.id}_{int(timezone.now().timestamp())}.jpg", upload)
        prof.avatar_url = default_storage.url(path)
        prof.save(update_fields=["avatar_url"])
        return Response({"ok": True, "avatar_url": prof.avatar_url})

    return Response({"detail": "Provide avatar_url or a file."},
                    status=status.HTTP_400_BAD_REQUEST)
