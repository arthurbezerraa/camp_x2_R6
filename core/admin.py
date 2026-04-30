from django.contrib import admin
from .models import (
    Player,
    Duo,
    Match,
    MatchPlayerStat,
    GroupX1,
    X1Match,
    X1MatchPlayerStat,
)


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('nome', 'grupo_x1', 'kills', 'deaths', 'kd_ratio', 'partidas_ganhas', 'rounds_ganhos')
    list_filter = ('grupo_x1',)
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


@admin.register(GroupX1)
class GroupX1Admin(admin.ModelAdmin):
    list_display = ('nome', 'ordem')
    ordering = ('ordem', 'nome')


class X1MatchPlayerStatInline(admin.TabularInline):
    model = X1MatchPlayerStat
    extra = 2
    max_num = 2
    fields = ('jogador', 'kills', 'deaths')
    verbose_name = 'Estatística do jogador'
    verbose_name_plural = 'Estatísticas dos jogadores'


@admin.register(X1Match)
class X1MatchAdmin(admin.ModelAdmin):
    list_display = ('jogador1', 'jogador2', 'rounds_jogador1', 'rounds_jogador2', 'prorrogacao', 'tipo', 'rodada', 'data')
    list_filter = ('tipo', 'prorrogacao', 'rodada')
    ordering = ('-data',)
    inlines = [X1MatchPlayerStatInline]
