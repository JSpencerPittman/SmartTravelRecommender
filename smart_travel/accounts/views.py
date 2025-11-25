from django.shortcuts import render, redirect  # type: ignore
from .forms import SignUpForm, LoginForm
from accounts.cqrs.queries import QueryFindUser


def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid() and form.save():
            return redirect("login")
    else:
        form = SignUpForm()
    return render(request, "signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user_name = form.cleaned_data["user_id"]
            password = form.cleaned_data["password"]

            result = QueryFindUser.execute(user_name=user_name, password=password)
            if not result["status"]:
                return render(request, "login.html", {"form": form})
            matches = result["data"]
            if len(matches) == 1:
                request.session["user_id"] = matches[0].id
                return redirect("/chat")
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})


def logout_view(request):
    assert request.method == "POST"
    return redirect("login")
