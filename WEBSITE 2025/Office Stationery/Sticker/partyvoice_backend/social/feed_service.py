"""
social/feed_service.py — Feed operations + follow graph + timeline assembly.

Like/comment counters are kept consistent with their rows via F() updates
inside transactions. Block relationships filter both timelines and discovery.
"""

from django.db import transaction as db_txn
from django.db.models import F, Q

from .feed import Post, PostComment, PostLike, Relationship


class FeedError(Exception):
    pass


@db_txn.atomic
def follow(*, user_id: int, target_id: int):
    if user_id == target_id:
        raise FeedError("You cannot follow yourself.")
    # cannot follow someone you've blocked or who blocked you
    if Relationship.objects.filter(
        Q(user_id=user_id, target_id=target_id, type=Relationship.Type.BLOCK) |
        Q(user_id=target_id, target_id=user_id, type=Relationship.Type.BLOCK)
    ).exists():
        raise FeedError("Cannot follow due to a block.")
    rel, _ = Relationship.objects.get_or_create(
        user_id=user_id, target_id=target_id, type=Relationship.Type.FOLLOW)
    return rel


def unfollow(*, user_id: int, target_id: int):
    Relationship.objects.filter(
        user_id=user_id, target_id=target_id, type=Relationship.Type.FOLLOW).delete()


@db_txn.atomic
def block(*, user_id: int, target_id: int):
    if user_id == target_id:
        raise FeedError("You cannot block yourself.")
    # blocking severs any follow edges both ways
    Relationship.objects.filter(
        Q(user_id=user_id, target_id=target_id) | Q(user_id=target_id, target_id=user_id),
        type=Relationship.Type.FOLLOW).delete()
    rel, _ = Relationship.objects.get_or_create(
        user_id=user_id, target_id=target_id, type=Relationship.Type.BLOCK)
    return rel


def create_post(*, author_id: int, body: str = "", media_urls: list | None = None) -> Post:
    body = (body or "").strip()
    media_urls = media_urls or []
    if not body and not media_urls:
        raise FeedError("Post needs text or media.")
    if len(media_urls) > 9:
        raise FeedError("Too many images (max 9).")
    # NOTE: text + image moderation hook lands in Phase 5
    return Post.objects.create(author_id=author_id, body=body, media_urls=media_urls)


@db_txn.atomic
def like_post(*, user_id: int, post_id: int):
    _, created = PostLike.objects.get_or_create(post_id=post_id, user_id=user_id)
    if created:
        Post.objects.filter(pk=post_id).update(like_count=F("like_count") + 1)
    return created


@db_txn.atomic
def unlike_post(*, user_id: int, post_id: int):
    deleted, _ = PostLike.objects.filter(post_id=post_id, user_id=user_id).delete()
    if deleted:
        Post.objects.filter(pk=post_id, like_count__gt=0).update(like_count=F("like_count") - 1)


@db_txn.atomic
def comment_post(*, author_id: int, post_id: int, body: str) -> PostComment:
    body = (body or "").strip()
    if not body:
        raise FeedError("Comment cannot be empty.")
    comment = PostComment.objects.create(post_id=post_id, author_id=author_id, body=body)
    Post.objects.filter(pk=post_id).update(comment_count=F("comment_count") + 1)
    return comment


def _blocked_ids(user_id: int):
    return set(Relationship.objects.filter(
        Q(user_id=user_id) | Q(target_id=user_id), type=Relationship.Type.BLOCK
    ).values_list("user_id", "target_id"))


def _excluded_user_ids(user_id: int) -> set:
    out = set()
    for a, b in _blocked_ids(user_id):
        out.add(a if a != user_id else b)
    return out


def following_timeline(*, user_id: int, before_id: int | None = None, limit: int = 20):
    """Posts from people the user follows, newest first."""
    following = Relationship.objects.filter(
        user_id=user_id, type=Relationship.Type.FOLLOW).values_list("target_id", flat=True)
    qs = Post.objects.filter(author_id__in=following, is_hidden=False)
    qs = qs.exclude(author_id__in=_excluded_user_ids(user_id))
    if before_id:
        qs = qs.filter(id__lt=before_id)
    return list(qs.select_related("author", "author__profile").order_by("-id")[:limit])


def discovery_feed(*, user_id: int, before_id: int | None = None, limit: int = 20):
    """The 'Square' — global recent feed, block-filtered."""
    qs = Post.objects.filter(is_hidden=False).exclude(author_id__in=_excluded_user_ids(user_id))
    if before_id:
        qs = qs.filter(id__lt=before_id)
    return list(qs.select_related("author", "author__profile").order_by("-id")[:limit])


def discovery_timeline_or_following(*, user_id: int, scope: str = "discovery",
                                    before_id: int | None = None, limit: int = 20):
    """Dispatcher used by the REST view: pick the timeline by scope."""
    if scope == "following":
        return following_timeline(user_id=user_id, before_id=before_id, limit=limit)
    return discovery_feed(user_id=user_id, before_id=before_id, limit=limit)
