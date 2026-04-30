from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('partidas/cadastrar/', views.cadastrar_partida, name='cadastrar_partida'),
    path('x1/', views.home_x1, name='home_x1'),
    path('x1/partidas/cadastrar/', views.cadastrar_partida_x1, name='cadastrar_partida_x1'),
]
