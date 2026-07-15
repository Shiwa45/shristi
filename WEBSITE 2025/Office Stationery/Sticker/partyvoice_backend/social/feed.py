"""
social/feed.py — Moments & Square (social feed) + follow graph.

Posts with text/media, likes, comments, and a follow relationship that powers
the "following" timeline. The "Square" (discovery) is the global recent/popular
feed. Reporting hooks live on every post for the Phase 5 T&S workstream.
"""

from django.conf import settings
from django.db import models


class Relationship(models.Model):
    """Directed follow / friend / block graph. One row per directed edge."""
    class Type(models.TextChoices):
        FOLLOW = "follow", "Follow"
        BLOCK = "block", "Block"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="outgoing_relations")
    target = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="incoming_relations")
    type = models.CharField(max_length=8, choices=Type.choices, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "target", "type")
        indexes = [models.Index(fields=["target", "type"])]

    @property
    def is_mutual_follow(self) -> bool:
        return Relationship.objects.filter(
            user=self.target, target=self.user, type=self.Type.FOLLOW).exists()


class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    body = models.CharField(max_length=1000, blank=True)
    media_urls = models.JSONField(default=list, blank=True)   # up to N image URLs
    # denormalized counters for cheap feed rendering
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    is_hidden = models.BooleanField(default=False, db_index=True)  # moderation
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["author", "-created_at"]),
                   models.Index(fields=["is_hidden", "-created_at"])]


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="post_likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user")


class PostComment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="post_comments")
    body = models.CharField(max_length=500)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
