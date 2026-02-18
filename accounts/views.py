from django.contrib.auth.views import LoginView, LogoutView

class AppLoginView(LoginView):
    """
    Custom Login View.
    
    Redirects authenticated users to the dashboard.
    """
    template_name = "accounts/login.html"
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return "/dashboard/"

class AppLogoutView(LogoutView):
    """
    Custom Logout View.
    
    Redirects to the login page after logout.
    """
    next_page = "/accounts/login/"
