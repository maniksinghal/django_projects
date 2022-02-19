from . import views
from django.urls import path

app_name = 'wordle'

urlpatterns = [
    path('', views.home, name='home'),
    path('solve_next', views.solve_next, name='solve_next') 
]