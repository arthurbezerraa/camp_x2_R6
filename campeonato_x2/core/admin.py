from django.contrib import admin
from .models import Player, Duo, Match, MatchPlayerStat


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('nome', 'kills', 'deaths', 'kd_ratio', 'partidas_ganhas', 'rounds_ganhos')
    search_fields = ('nome',)
    ordering = ('nome',)


@admin.register(Duo)
class DuoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'jogador1', 'jogador2', 'pontos', 'vitorias', 'derrotas', 'saldo_rounds')
    search_fields = ('nome',)
    ordering = ('nome',)


class MatchPlayerStatInline(admin.TabularInline):
    model = MatchPlayerStat
    extra = 4
    max_num = 4
    fields = ('jogador', 'kills', 'deaths')
    verbose_name = 'Estatística do jogador'
    verbose_name_plural = 'Estatísticas dos jogadores'


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('dupla1', 'dupla2', 'rounds_dupla1', 'rounds_dupla2', 'prorrogacao', 'tipo', 'rodada', 'data')
    list_filter = ('tipo', 'prorrogacao', 'rodada')
    ordering = ('-data',)
    inlines = [MatchPlayerStatInline]
