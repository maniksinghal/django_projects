from . import views
from django.urls import path

app_name = 'auth_program'

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_user, name='signup_user'),
    path('logout/', views.logout_user, name='logout_user'), 
    path('login/', views.login_user, name='login_user'), 
    path('current/', views.logged_in, name='logged_in'),
]