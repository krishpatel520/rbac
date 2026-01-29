from django.contrib.auth.views import LoginView, LogoutView

class AppLoginView(LoginView):
    template_name = "accounts/login.html"

class AppLogoutView(LogoutView):
    next_page = "/accounts/login/"
