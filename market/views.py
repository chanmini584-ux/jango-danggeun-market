from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import SignUpForm
from .models import Profile


def main(request):
    return render(request, "market/main.html")


@require_http_methods(["GET", "POST"])
def signup(request):
    if request.user.is_authenticated:
        return redirect("main")

    form = SignUpForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            user = form.save()
        except IntegrityError:
            # A concurrent signup may reserve an ID or phone after validation.
            if User.objects.filter(username=form.cleaned_data["username"]).exists():
                form.add_error("username", "이미 사용 중인 아이디입니다.")
            if Profile.objects.filter(phone=form.cleaned_data["phone"]).exists():
                form.add_error("phone", "이미 사용 중인 휴대폰번호입니다.")
            if not form.errors:
                raise
        else:
            login(request, user)
            return redirect("main")

    return render(request, "market/signup.html", {"form": form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("main")

    username = ""
    if request.method == "POST":
        username = request.POST.get("username", "")
        user = authenticate(
            request,
            username=username,
            password=request.POST.get("password", ""),
        )
        if user is not None:
            login(request, user)
            return redirect("main")
        messages.error(request, "아이디 또는 비밀번호가 올바르지 않습니다.")

    return render(request, "market/login.html", {"username": username})


@require_http_methods(["GET", "POST"])
def logout_view(request):
    if request.method == "POST":
        logout(request)
    return redirect("main")
