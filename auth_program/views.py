from sqlite3 import IntegrityError
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib.auth import login, logout, authenticate
import logging

logger = logging.getLogger(__name__)

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(name)-12s %(levelname)-8s %(message)s'
        },
        'file': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'file',
            'filename': '/tmp/debug.log'
        }
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['console', 'file']
        }
    }
})

# Create your views here.
def signup_user(request):
    logger.info("Got some request from user")
    if request.method == 'GET':
        #User landed on sign-up page
        return render(request, 'auth_program/signup_user.html', {'form':UserCreationForm()})
    else:
        #User submitted a sign-up request
        logger.info("Got a POST response from user while signing up")
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(request.POST['username'],
                         password=request.POST['password1'])
                user.save()
                login(request, user)  #Log-in the user
                return redirect('auth_program:logged_in')
            except IntegrityError:   #User already exists
                return render(request, 'auth_program/signup_user.html', 
               {'form':UserCreationForm(), 'err_str':"Username already taken"})
        else:
            return render(request, 'auth_program/signup_user.html', 
               {'form':UserCreationForm(), 'err_str':"Passwords do not match"})

def logged_in(request):
    return render(request, "auth_program/user_info.html")

def home(request):
    return render(request, 'auth_program/home.html')

def login_user(request):
    logger.info("Got some request from user")
    if request.method == 'GET':
        #User landed on sign-up page
        return render(request, 'auth_program/login.html', {'form':AuthenticationForm()})
    else:
        user = authenticate(request, username=request.POST['username'],
                          password=request.POST['password'])
        if not user:
           return render(request, 'auth_program/login.html', {'form':AuthenticationForm(),
                             'err_str':"Username/password does not match"})
        else:
            login(request, user)
            return redirect('auth_program:logged_in')

def logout_user(request):

    #Should be a POST request. Browser would try to pre-load
    #GET requests while loading a page for faster performance
    # and may end up logging user out in this case.
    if request.method == "POST":
       logout(request)
       return redirect('auth_program:home') 
