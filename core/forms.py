from django import forms
from .models import Match


class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['tipo', 'dupla1', 'dupla2', 'rounds_dupla1', 'rounds_dupla2', 'prorrogacao', 'rodada']
        widgets = {
            'tipo': forms.RadioSelect(),
            'rounds_dupla1': forms.NumberInput(attrs={'min': 0, 'max': 8}),
            'rounds_dupla2': forms.NumberInput(attrs={'min': 0, 'max': 8}),
            'rodada': forms.NumberInput(attrs={'min': 1, 'max': 7}),
        }
        labels = {
            'tipo': 'Tipo de partida',
            'dupla1': 'Dupla 1',
            'dupla2': 'Dupla 2',
            'rounds_dupla1': 'Rounds — Dupla 1',
            'rounds_dupla2': 'Rounds — Dupla 2',
            'prorrogacao': 'Houve prorrogação?',
            'rodada': 'Rodada (1–7)',
        }

    def clean(self):
        cleaned = super().clean()
        instance = self.instance
        instance.tipo = cleaned.get('tipo', 'PONTOS_CORRIDOS')
        instance.dupla1 = cleaned.get('dupla1')
        instance.dupla2 = cleaned.get('dupla2')
        instance.rounds_dupla1 = cleaned.get('rounds_dupla1')
        instance.rounds_dupla2 = cleaned.get('rounds_dupla2')
        instance.prorrogacao = cleaned.get('prorrogacao', False)

        try:
            instance.clean()
        except Exception as e:
            raise forms.ValidationError(e)

        return cleaned
