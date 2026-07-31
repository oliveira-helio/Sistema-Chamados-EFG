from django.shortcuts import redirect
from django.urls import reverse


class FirstAccessPasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated and getattr(user, "first_access", False):
            allowed_paths = {
                reverse("first_access_password_change"),
                reverse("logout"),
            }
            if request.path not in allowed_paths and not request.path.startswith(("/static/", "/media/")):
                return redirect("first_access_password_change")
        return self.get_response(request)
