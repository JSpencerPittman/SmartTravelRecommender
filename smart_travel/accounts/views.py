from django.shortcuts import render,redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm,LoginForm
from chat.models import User
from django.contrib import messages
# Create your views here.


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            request.session['user_id'] = user.id
            request.session['user_name'] = user.user_name
            request.session['first_name'] = user.first_name
            request.session['last_name'] = user.last_name
            return redirect('select')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
           user_name = form.cleaned_data['user_id']
           password = form.cleaned_data['password']
           try: 
            user = User.objects.get(user_name=user_name, password=password)
            if user is not None:
                request.session['user_id'] = user.id
                request.session['user_name'] = user.user_name
                request.session['first_name'] = user.first_name
                request.session['last_name'] = user.last_name
                return redirect('select')
           except User.DoesNotExist:
               messages.error(request, "Invalid username or password")
            
               
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})
