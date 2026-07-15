from django.contrib import admin

from .families import Family, FamilyJoinRequest, FamilyMember
from .feed import Post, PostComment, PostLike, Relationship


class FamilyMemberInline(admin.TabularInline):
    model = FamilyMember
    extra = 0
    raw_id_fields = ("user",)


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "funds", "exp", "created_by", "created_at")
    search_fields = ("name",)
    inlines = [FamilyMemberInline]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "short_body", "like_count", "comment_count",
                    "is_hidden", "created_at")
    list_filter = ("is_hidden", "created_at")
    search_fields = ("author__username", "body")
    date_hierarchy = "created_at"
    actions = ("hide_posts", "unhide_posts")

    @admin.display(description="body")
    def short_body(self, obj):
        return (obj.body[:60] + "…") if len(obj.body) > 60 else obj.body

    @admin.action(description="Hide selected posts")
    def hide_posts(self, request, queryset):
        queryset.update(is_hidden=True)

    @admin.action(description="Unhide selected posts")
    def unhide_posts(self, request, queryset):
        queryset.update(is_hidden=False)


for _m in (FamilyMember, FamilyJoinRequest, PostComment, PostLike, Relationship):
    admin.site.register(_m)
