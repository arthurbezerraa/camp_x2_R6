from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError


class Player(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = 'Jogador'
        verbose_name_plural = 'Jogadores'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    @property
    def kills(self):
        return self.match_stats.aggregate(total=Sum('kills'))['total'] or 0

    @property
    def deaths(self):
        return self.match_stats.aggregate(total=Sum('deaths'))['total'] or 0

    @property
    def kd_ratio(self):
        d = self.deaths
        if d == 0:
            return float(self.kills)
        return round(self.kills / d, 2)

    def _get_duo(self):
        return (
            self.duplas_como_j1.first()
            or self.duplas_como_j2.first()
        )

    @property
    def partidas_ganhas(self):
        duo = self._get_duo()
        if not duo:
            return 0
        return duo.vitorias

    @property
    def rounds_ganhos(self):
        duo = self._get_duo()
        if not duo:
            return 0
        return duo.rounds_ganhos


class Duo(models.Model):
    nome = models.CharField(max_length=80, unique=True)
    jogador1 = models.ForeignKey(
        Player, on_delete=models.PROTECT, related_name='duplas_como_j1'
    )
    jogador2 = models.ForeignKey(
        Player, on_delete=models.PROTECT, related_name='duplas_como_j2'
    )

    class Meta:
        verbose_name = 'Dupla'
        verbose_name_plural = 'Duplas'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def _partidas_finalizadas(self):
        return Match.objects.filter(
            models.Q(dupla1=self) | models.Q(dupla2=self),
            tipo='PONTOS_CORRIDOS',
        )

    @property
    def partidas_jogadas(self):
        return self._partidas_finalizadas().count()

    @property
    def vitorias(self):
        count = 0
        for m in self._partidas_finalizadas():
            if m.vencedora() == self:
                count += 1
        return count

    @property
    def derrotas(self):
        return self.partidas_jogadas - self.vitorias

    @property
    def pontos(self):
        total = 0
        for m in self._partidas_finalizadas():
            if m.dupla1 == self:
                total += m.pontos_dupla1()
            else:
                total += m.pontos_dupla2()
        return total

    @property
    def rounds_ganhos(self):
        total = 0
        for m in self._partidas_finalizadas():
            if m.dupla1 == self:
                total += m.rounds_dupla1
            else:
                total += m.rounds_dupla2
        return total

    @property
    def rounds_perdidos(self):
        total = 0
        for m in self._partidas_finalizadas():
            if m.dupla1 == self:
                total += m.rounds_dupla2
            else:
                total += m.rounds_dupla1
        return total

    @property
    def saldo_rounds(self):
        return self.rounds_ganhos - self.rounds_perdidos


class Match(models.Model):
    TIPO_CHOICES = [
        ('PONTOS_CORRIDOS', 'Pontos Corridos'),
        ('MATA_MATA', 'Mata Mata'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='PONTOS_CORRIDOS')
    dupla1 = models.ForeignKey(
        Duo, on_delete=models.PROTECT, related_name='partidas_como_d1'
    )
    dupla2 = models.ForeignKey(
        Duo, on_delete=models.PROTECT, related_name='partidas_como_d2'
    )
    rounds_dupla1 = models.IntegerField()
    rounds_dupla2 = models.IntegerField()
    prorrogacao = models.BooleanField(default=False)
    rodada = models.IntegerField(null=True, blank=True)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Partida'
        verbose_name_plural = 'Partidas'
        ordering = ['-data']

    def __str__(self):
        return f'{self.dupla1} vs {self.dupla2} ({self.rounds_dupla1}×{self.rounds_dupla2})'

    def clean(self):
        if self.tipo != 'PONTOS_CORRIDOS':
            return

        if self.dupla1_id and self.dupla2_id and self.dupla1_id == self.dupla2_id:
            raise ValidationError('A dupla 1 e a dupla 2 não podem ser a mesma.')

        r1 = self.rounds_dupla1
        r2 = self.rounds_dupla2

        if r1 is None or r2 is None:
            return

        if self.prorrogacao:
            valid = (
                (r1 == 8 and r2 in (6, 7)) or
                (r2 == 8 and r1 in (6, 7))
            )
            if not valid:
                raise ValidationError(
                    'Com prorrogação, o placar deve ser 8×6 ou 8×7 (em qualquer direção).'
                )
        else:
            valid = (
                (r1 == 7 and 0 <= r2 <= 5) or
                (r2 == 7 and 0 <= r1 <= 5)
            )
            if not valid:
                raise ValidationError(
                    'Sem prorrogação, o placar deve ser 7×N (N entre 0 e 5) em qualquer direção.'
                )

    def vencedora(self):
        if self.rounds_dupla1 > self.rounds_dupla2:
            return self.dupla1
        return self.dupla2

    def pontos_dupla1(self):
        if self.rounds_dupla1 > self.rounds_dupla2:
            return 2 if self.prorrogacao else 3
        return 1 if self.prorrogacao else 0

    def pontos_dupla2(self):
        if self.rounds_dupla2 > self.rounds_dupla1:
            return 2 if self.prorrogacao else 3
        return 1 if self.prorrogacao else 0


class MatchPlayerStat(models.Model):
    partida = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='stats')
    jogador = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='match_stats')
    kills = models.IntegerField(default=0)
    deaths = models.IntegerField(default=0)

    class Meta:
        unique_together = [('partida', 'jogador')]
        verbose_name = 'Estatística de Partida'
        verbose_name_plural = 'Estatísticas de Partida'

    def __str__(self):
        return f'{self.jogador} — {self.partida}'
