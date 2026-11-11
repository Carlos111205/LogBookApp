from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
urlpatterns=[
    path("accounts/login/",auth_views.LoginView.as_view(template_name="logbook/login.html",redirect_authenticated_user=True),name="login"),
    path("accounts/logout/",auth_views.LogoutView.as_view(next_page="login"),name="logout"),
    path("accounts/signup/",views.signup,name="signup"),
    path("",views.dashboard,name="dashboard"),path("profile/",views.profile,name="profile"),
    path("logbook/",views.logbook,name="logbook"),path("logbook/<int:pk>/delete/",views.delete_entry,name="delete_entry"),
    path("report/",views.report,name="report"),path("download/<str:kind>/<str:fmt>/",views.download,name="download")]
