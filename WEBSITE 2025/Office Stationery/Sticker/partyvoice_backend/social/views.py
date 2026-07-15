"""
social/views.py — REST API for families + feed (Phase 3).

Thin views over the already-tested service layer (family_service, feed_service).
These expose exactly the endpoints the Flutter client calls:
  /api/families/                 GET list, POST create
  /api/families/mine             GET my family (404 if none)
  /api/families/<id>/members     GET members
  /api/families/<id>/join        POST request to join
  /api/families/contribute       POST contribute coins
  /api/feed                      GET (?scope=discovery|following)
  /api/posts                     POST create
  /api/posts/<id>/like|unlike    POST
  /api/posts/<id>/comments       GET list, POST add
  /api/follow                    POST
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from .families import Family, FamilyMember
from .family_service import (
    FamilyError, contribute, create_family, request_join,
)
from .feed import Post, PostComment
from .feed_service import (
    FeedError, comment_post, create_post, discovery_timeline_or_following,
    follow, like_post, unlike_post,
)


def _family_json(family: Family, user_id=None):
    my_role = None
    if user_id is not None:
        m = FamilyMember.objects.filter(family=family, user_id=user_id).first()
        my_role = m.role if m else None
    return {
        "id": family.id,
        "name": family.name,
        "logo_url": family.logo_url,
        "notice": family.notice,
        "level": family.level,
        "funds": family.funds,
        "member_count": family.members.count(),
        "member_capacity": family.member_capacity,
        "can_have_voice_room": family.can_have_voice_room,
        "my_role": my_role,
    }


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def families(request):
    if request.method == "POST":
        try:
            family = create_family(
                founder_id=request.user.id,
                name=(request.data.get("name") or "").strip(),
                logo_url=request.data.get("logo_url", ""),
            )
        except FamilyError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(_family_json(family, request.user.id), status=status.HTTP_201_CREATED)

    q = request.query_params.get("q")
    qs = Family.objects.all().order_by("-level", "-funds")
    if q:
        qs = qs.filter(name__icontains=q)
    return Response([_family_json(f) for f in qs[:50]])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_family(request):
    m = FamilyMember.objects.filter(user_id=request.user.id).select_related("family").first()
    if not m:
        return Response({"detail": "Not in a family."}, status=status.HTTP_404_NOT_FOUND)
    return Response(_family_json(m.family, request.user.id))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def family_members(request, family_id):
    members = (FamilyMember.objects
               .filter(family_id=family_id)
               .select_related("user", "user__profile")
               .order_by("-role", "-contribution"))
    out = []
    for m in members:
        prof = getattr(m.user, "profile", None)
        out.append({
            "user_id": m.user.public_id.hex,
            "name": prof.display_name if prof else m.user.username,
            "avatar_url": prof.avatar_url if prof else "",
            "role": m.role,
            "contribution": m.contribution,
        })
    return Response(out)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def family_join(request, family_id):
    try:
        request_join(user_id=request.user.id, family_id=family_id)
    except FamilyError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"ok": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def family_contribute(request):
    try:
        amount = int(request.data.get("amount", 0))
        family = contribute(user_id=request.user.id, amount=amount)
    except (FamilyError, ValueError) as e:
        return Response({"detail": str(e) or "Invalid amount."}, status=status.HTTP_400_BAD_REQUEST)
    return Response(_family_json(family, request.user.id))


def _post_json(post: Post, viewer_id=None):
    prof = getattr(post.author, "profile", None)
    liked = False
    if viewer_id is not None:
        liked = post.likes.filter(user_id=viewer_id).exists()
    return {
        "id": post.id,
        "author_id": post.author.public_id.hex,
        "author_name": prof.display_name if prof else post.author.username,
        "author_avatar": prof.avatar_url if prof else "",
        "body": post.body,
        "media_urls": post.media_urls,
        "like_count": post.like_count,
        "comment_count": post.comment_count,
        "liked": liked,
        "created_at": post.created_at.isoformat(),
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def feed(request):
    scope = request.query_params.get("scope", "discovery")
    before_id = request.query_params.get("before_id")
    before_id = int(before_id) if before_id else None
    posts = discovery_timeline_or_following(
        user_id=request.user.id, scope=scope, before_id=before_id)
    return Response([_post_json(p, request.user.id) for p in posts])


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def posts(request):
    try:
        post = create_post(
            author_id=request.user.id,
            body=request.data.get("body", ""),
            media_urls=request.data.get("media_urls", []),
        )
    except FeedError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(_post_json(post, request.user.id), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def post_like(request, post_id):
    like_post(user_id=request.user.id, post_id=post_id)
    return Response({"ok": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def post_unlike(request, post_id):
    unlike_post(user_id=request.user.id, post_id=post_id)
    return Response({"ok": True})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def post_comments(request, post_id):
    if request.method == "POST":
        try:
            comment_post(author_id=request.user.id, post_id=post_id,
                         body=request.data.get("body", ""))
        except FeedError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"ok": True}, status=status.HTTP_201_CREATED)

    comments = (PostComment.objects.filter(post_id=post_id, is_hidden=False)
                .select_related("author", "author__profile"))
    out = []
    for c in comments:
        prof = getattr(c.author, "profile", None)
        out.append({
            "author_name": prof.display_name if prof else c.author.username,
            "body": c.body,
            "created_at": c.created_at.isoformat(),
        })
    return Response(out)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def follow_user(request):
    target_public_id = request.data.get("user_id")
    target = User.objects.filter(public_id=target_public_id).first()
    if not target:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    try:
        follow(user_id=request.user.id, target_id=target.id)
    except FeedError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"ok": True})
