from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Duo, Player, Match, MatchPlayerStat
from .forms import MatchForm


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

    recent_qs = (
        Match.objects
        .filter(tipo='PONTOS_CORRIDOS')
        .select_related(
            'dupla1', 'dupla2',
            'dupla1__jogador1', 'dupla1__jogador2',
            'dupla2__jogador1', 'dupla2__jogador2',
        )
        .prefetch_related('stats__jogador')
        .order_by('-data')[:4]
    )

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

    return render(request, 'core/home.html', {
        'duos': duos,
        'players': players,
        'match_data': match_data,
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
