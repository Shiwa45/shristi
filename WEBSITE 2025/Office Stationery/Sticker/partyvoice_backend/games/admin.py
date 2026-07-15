from django.contrib import admin

from .models import GameDefinition, GamePlayer, GameSession


@admin.register(GameDefinition)
class GameDefinitionAdmin(admin.ModelAdmin):
    list_display = [f.name for f in GameDefinition._meta.fields][:6]


for _m in (GameSession, GamePlayer):
    admin.site.register(_m)
