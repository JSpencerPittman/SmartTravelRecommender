from django.shortcuts import render, redirect
from .forms import SignUpForm, LoginForm
from accounts.models import AccountModel
from django.contrib import messages  # type: ignore


def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            account = form.save()
            request.session["user_id"] = account.id
            request.session["user_name"] = account.user_name
            request.session["first_name"] = account.first_name
            request.session["last_name"] = account.last_name
            return redirect("select")
    else:
        form = SignUpForm()
    return render(request, "signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user_name = form.cleaned_data["user_id"]
            password = form.cleaned_data["password"]
            try:
                account = AccountModel.objects.get(
                    user_name=user_name, password=password
                )
                if account is not None:
                    request.session["user_id"] = account.id
                    request.session["user_name"] = account.user_name
                    request.session["first_name"] = account.first_name
                    request.session["last_name"] = account.last_name
                    return redirect("select")
            except AccountModel.DoesNotExist:
                messages.error(request, "Invalid username or password")

    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})
