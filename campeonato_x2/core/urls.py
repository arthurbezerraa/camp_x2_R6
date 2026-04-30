from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('partidas/cadastrar/', views.cadastrar_partida, name='cadastrar_partida'),
]
