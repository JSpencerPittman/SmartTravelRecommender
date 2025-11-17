from django.shortcuts import render, redirect  # type: ignore
from .forms import SignUpForm, LoginForm
from accounts.models import AccountModel


def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            account = form.save()
            request.session["user_id"] = account.id
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
            matches = AccountModel.find_matching_user(
                user_name=user_name, password=password
            )
            if len(matches) == 1:
                request.session["user_id"] = matches[0].id
                return redirect("select")
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})
