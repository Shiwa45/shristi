"""Root URLconf for the PartyVoice backend."""

from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from rooms.views import RoomViewSet
from rtc.views import RtcTokenView
from rooms.pk_service import ChatTokenView
from economy.views import (
    WalletView, GiftCatalogView, SendGiftView, IAPValidateView, leaderboard_view,
)
from admin_tools.views import review_queue, resolve_case, dismiss_case
from social import views as social_views
from rooms import profile_theme_views as room_extra
from rooms import game_views
from games import spy_views
from games import draw_views
from accounts import views as account_views

router = DefaultRouter()
router.register(r"rooms", RoomViewSet, basename="room")

admin.site.site_header = "PartyVoice Admin"
admin.site.site_title = "PartyVoice Admin"
admin.site.index_title = "Manage gifts, themes, VIP, offers, rooms & more"

urlpatterns = [
    path("admin/", admin.site.urls),

    # auth (phone OTP)
    path("api/auth/phone/otp", account_views.request_otp, name="auth-otp"),
    path("api/auth/phone/verify", account_views.verify_otp, name="auth-verify"),
    path("api/me", account_views.me, name="me"),
    path("api/me/avatar", account_views.set_avatar, name="me-avatar"),

    # REST API
    path("api/", include(router.urls)),

    # RTC + chat tokens (ZEGOCLOUD)
    path("api/rtc/token", RtcTokenView.as_view(), name="rtc-token"),
    path("api/chat/token", ChatTokenView.as_view(), name="chat-token"),

    # economy
    path("api/wallet", WalletView.as_view(), name="wallet"),
    path("api/gifts", GiftCatalogView.as_view(), name="gift-catalog"),
    path("api/gifts/send", SendGiftView.as_view(), name="gift-send"),
    path("api/iap/validate", IAPValidateView.as_view(), name="iap-validate"),
    path("api/leaderboard", leaderboard_view, name="leaderboard"),

    # moderation (staff)
    path("api/mod/queue", review_queue, name="mod-queue"),
    path("api/mod/cases/<int:case_id>/resolve", resolve_case, name="mod-resolve"),
    path("api/mod/cases/<int:case_id>/dismiss", dismiss_case, name="mod-dismiss"),

    # families (Phase 3)
    path("api/families/", social_views.families, name="families"),
    path("api/families/mine", social_views.my_family, name="family-mine"),
    path("api/families/contribute", social_views.family_contribute, name="family-contribute"),
    path("api/families/<int:family_id>/members", social_views.family_members, name="family-members"),
    path("api/families/<int:family_id>/join", social_views.family_join, name="family-join"),

    # feed / Moments (Phase 3)
    path("api/feed", social_views.feed, name="feed"),
    path("api/posts", social_views.posts, name="posts"),
    path("api/posts/<int:post_id>/like", social_views.post_like, name="post-like"),
    path("api/posts/<int:post_id>/unlike", social_views.post_unlike, name="post-unlike"),
    path("api/posts/<int:post_id>/comments", social_views.post_comments, name="post-comments"),
    path("api/follow", social_views.follow_user, name="follow"),

    # profiles + room themes + room admin (room rebuild)
    path("api/users/<str:public_id>", room_extra.user_profile, name="user-profile"),
    path("api/room-themes", room_extra.room_themes, name="room-themes"),
    path("api/room-themes/<str:key>/buy", room_extra.buy_theme, name="room-theme-buy"),
    path("api/rooms/<str:room_id>/apply-theme", room_extra.apply_theme, name="room-apply-theme"),
    path("api/rooms/<str:room_id>/admins", room_extra.room_admins, name="room-admins"),

    # auction rooms (live bidding)
    path("api/rooms/<str:room_id>/auction", game_views.auction_state, name="auction-state"),
    path("api/rooms/<str:room_id>/auction/create", game_views.auction_create, name="auction-create"),
    path("api/rooms/<str:room_id>/auction/bid", game_views.auction_bid, name="auction-bid"),
    path("api/rooms/<str:room_id>/auction/close", game_views.auction_close, name="auction-close"),

    # gaming rooms (lucky spin)
    path("api/rooms/<str:room_id>/spin", game_views.spin_state, name="spin-state"),
    path("api/rooms/<str:room_id>/spin/open", game_views.spin_open, name="spin-open"),
    path("api/rooms/<str:room_id>/spin/bet", game_views.spin_bet, name="spin-bet"),
    path("api/rooms/<str:room_id>/spin/settle", game_views.spin_settle, name="spin-settle"),

    # Who's the Spy (in-room party game)
    path("api/rooms/<str:room_id>/spy", spy_views.spy_state, name="spy-state"),
    path("api/rooms/<str:room_id>/spy/create", spy_views.spy_create, name="spy-create"),
    path("api/rooms/<str:room_id>/spy/join", spy_views.spy_join, name="spy-join"),
    path("api/rooms/<str:room_id>/spy/start", spy_views.spy_start, name="spy-start"),
    path("api/rooms/<str:room_id>/spy/my-role", spy_views.spy_my_role, name="spy-role"),
    path("api/rooms/<str:room_id>/spy/describe", spy_views.spy_describe, name="spy-describe"),
    path("api/rooms/<str:room_id>/spy/vote", spy_views.spy_vote, name="spy-vote"),
    path("api/rooms/<str:room_id>/spy/leave", spy_views.spy_leave, name="spy-leave"),

    # Draw & Guess (strokes + guesses go over the WebSocket, not here)
    path("api/rooms/<str:room_id>/draw", draw_views.draw_state, name="draw-state"),
    path("api/rooms/<str:room_id>/draw/create", draw_views.draw_create, name="draw-create"),
    path("api/rooms/<str:room_id>/draw/join", draw_views.draw_join, name="draw-join"),
    path("api/rooms/<str:room_id>/draw/start", draw_views.draw_start, name="draw-start"),
    path("api/rooms/<str:room_id>/draw/my-word", draw_views.draw_my_word, name="draw-word"),
    path("api/rooms/<str:room_id>/draw/end-round", draw_views.draw_end_round, name="draw-end"),
    path("api/rooms/<str:room_id>/draw/leave", draw_views.draw_leave, name="draw-leave"),
]
