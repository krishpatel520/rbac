from django.contrib.auth.views import LoginView, LogoutView

class AppLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return "/dashboard/"

class AppLogoutView(LogoutView):
    next_page = "/accounts/login/"
