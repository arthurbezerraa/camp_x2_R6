from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q
from .models import (
    Duo,
    Player,
    Match,
    MatchPlayerStat,
    GroupX1,
    X1Match,
    X1MatchPlayerStat,
)
from .forms import MatchForm, X1MatchForm


def _build_player_stat(stats_map, player):
    s = stats_map.get(player.id)
    return {
        'player': player,
        'kills': s.kills if s else None,
        'deaths': s.deaths if s else None,
    }


def home(request):
    duos = list(Duo.objects.prefetch_related(
        'partidas_como_d1', 'partidas_como_d2'
    ).all())
    duos.sort(key=lambda d: (-d.pontos, -d.saldo_rounds))

    players = list(Player.objects.all())
    players.sort(key=lambda p: -p.kd_ratio)

    filter_dupla = (request.GET.get('dupla') or '').strip()
    filter_jogador = (request.GET.get('jogador') or '').strip()
    filter_ot = request.GET.get('ot') == '1'
    is_filtered = bool(filter_dupla or filter_jogador or filter_ot)

    recent_qs = Match.objects.filter(tipo='PONTOS_CORRIDOS')

    if filter_dupla.isdigit():
        recent_qs = recent_qs.filter(
            Q(dupla1_id=filter_dupla) | Q(dupla2_id=filter_dupla)
        )
    if filter_jogador.isdigit():
        recent_qs = recent_qs.filter(
            Q(dupla1__jogador1_id=filter_jogador)
            | Q(dupla1__jogador2_id=filter_jogador)
            | Q(dupla2__jogador1_id=filter_jogador)
            | Q(dupla2__jogador2_id=filter_jogador)
        )
    if filter_ot:
        recent_qs = recent_qs.filter(prorrogacao=True)

    recent_qs = (
        recent_qs
        .select_related(
            'dupla1', 'dupla2',
            'dupla1__jogador1', 'dupla1__jogador2',
            'dupla2__jogador1', 'dupla2__jogador2',
        )
        .prefetch_related('stats__jogador')
        .order_by('-data')
    )
    if not is_filtered:
        recent_qs = recent_qs[:4]

    match_data = []
    for m in recent_qs:
        stats_map = {s.jogador_id: s for s in m.stats.all()}
        match_data.append({
            'match': m,
            'dupla1_stats': [
                _build_player_stat(stats_map, m.dupla1.jogador1),
                _build_player_stat(stats_map, m.dupla1.jogador2),
            ],
            'dupla2_stats': [
                _build_player_stat(stats_map, m.dupla2.jogador1),
                _build_player_stat(stats_map, m.dupla2.jogador2),
            ],
        })

    duos_filter = list(Duo.objects.order_by('nome'))
    players_filter = list(Player.objects.order_by('nome'))

    return render(request, 'core/home.html', {
        'duos': duos,
        'players': players,
        'match_data': match_data,
        'duos_filter': duos_filter,
        'players_filter': players_filter,
        'filter_dupla': filter_dupla,
        'filter_jogador': filter_jogador,
        'filter_ot': filter_ot,
        'is_filtered': is_filtered,
        'match_count': len(match_data),
    })


def _build_duos_data(duos):
    return {
        str(d.id): {
            'j1': {'id': d.jogador1_id, 'nome': d.jogador1.nome},
            'j2': {'id': d.jogador2_id, 'nome': d.jogador2.nome},
        }
        for d in duos
    }


def _collect_prev_stats(post):
    return {
        key: value for key, value in post.items()
        if key.startswith('stat_')
    }


def _parse_stat_int(raw):
    if raw is None or str(raw).strip() == '':
        return 0
    try:
        return max(int(raw), 0)
    except (TypeError, ValueError):
        return 0


def cadastrar_partida(request):
    duos = list(Duo.objects.select_related('jogador1', 'jogador2').order_by('nome'))
    duos_data = _build_duos_data(duos)
    prev_stats = {}

    if request.method == 'POST':
        form = MatchForm(request.POST)
        if form.is_valid():
            match = form.save()
            jogador_ids = {
                match.dupla1.jogador1_id,
                match.dupla1.jogador2_id,
                match.dupla2.jogador1_id,
                match.dupla2.jogador2_id,
            }
            for player_id in jogador_ids:
                MatchPlayerStat.objects.create(
                    partida=match,
                    jogador_id=player_id,
                    kills=_parse_stat_int(request.POST.get(f'stat_{player_id}_kills')),
                    deaths=_parse_stat_int(request.POST.get(f'stat_{player_id}_deaths')),
                )
            messages.success(request, 'Partida cadastrada com sucesso.')
            return redirect('home')
        prev_stats = _collect_prev_stats(request.POST)
    else:
        form = MatchForm(initial={'tipo': 'PONTOS_CORRIDOS'})

    return render(request, 'core/cadastrar_partida.html', {
        'form': form,
        'duos': duos,
        'duos_data': duos_data,
        'prev_stats': prev_stats,
    })


def _build_x1_player_stat(stats_map, player):
    s = stats_map.get(player.id)
    return {
        'player': player,
        'kills': s.kills if s else None,
        'deaths': s.deaths if s else None,
    }


def home_x1(request):
    grupos_qs = GroupX1.objects.prefetch_related('jogadores').all()
    grupos = []
    for g in grupos_qs:
        grupos.append({
            'grupo': g,
            'jogadores': g.jogadores_classificados(),
        })

    players = list(Player.objects.exclude(grupo_x1__isnull=True))
    players.sort(key=lambda p: -p.x1_kd_ratio)

    filter_jogador = (request.GET.get('jogador') or '').strip()
    filter_ot = request.GET.get('ot') == '1'
    is_filtered = bool(filter_jogador or filter_ot)

    recent_qs = X1Match.objects.filter(tipo='PONTOS_CORRIDOS')

    if filter_jogador.isdigit():
        recent_qs = recent_qs.filter(
            Q(jogador1_id=filter_jogador) | Q(jogador2_id=filter_jogador)
        )
    if filter_ot:
        recent_qs = recent_qs.filter(prorrogacao=True)

    recent_qs = (
        recent_qs
        .select_related('jogador1', 'jogador2')
        .prefetch_related('stats__jogador')
        .order_by('-data')
    )
    if not is_filtered:
        recent_qs = recent_qs[:4]

    match_data = []
    for m in recent_qs:
        stats_map = {s.jogador_id: s for s in m.stats.all()}
        match_data.append({
            'match': m,
            'jogador1_stat': _build_x1_player_stat(stats_map, m.jogador1),
            'jogador2_stat': _build_x1_player_stat(stats_map, m.jogador2),
        })

    players_filter = list(
        Player.objects.exclude(grupo_x1__isnull=True).order_by('nome')
    )

    return render(request, 'core/home_x1.html', {
        'grupos': grupos,
        'players': players,
        'match_data': match_data,
        'players_filter': players_filter,
        'filter_jogador': filter_jogador,
        'filter_ot': filter_ot,
        'is_filtered': is_filtered,
        'match_count': len(match_data),
    })


def _build_players_data(players):
    return {
        str(p.id): {'id': p.id, 'nome': p.nome}
        for p in players
    }


def cadastrar_partida_x1(request):
    players = list(Player.objects.order_by('nome'))
    players_data = _build_players_data(players)
    prev_stats = {}

    if request.method == 'POST':
        form = X1MatchForm(request.POST)
        if form.is_valid():
            match = form.save()
            jogador_ids = {match.jogador1_id, match.jogador2_id}
            for player_id in jogador_ids:
                X1MatchPlayerStat.objects.create(
                    partida=match,
                    jogador_id=player_id,
                    kills=_parse_stat_int(request.POST.get(f'stat_{player_id}_kills')),
                    deaths=_parse_stat_int(request.POST.get(f'stat_{player_id}_deaths')),
                )
            messages.success(request, 'Partida X1 cadastrada com sucesso.')
            return redirect('home_x1')
        prev_stats = _collect_prev_stats(request.POST)
    else:
        form = X1MatchForm(initial={'tipo': 'PONTOS_CORRIDOS'})

    return render(request, 'core/cadastrar_partida_x1.html', {
        'form': form,
        'players': players,
        'players_data': players_data,
        'prev_stats': prev_stats,
    })
