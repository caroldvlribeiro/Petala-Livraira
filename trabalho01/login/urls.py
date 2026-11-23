from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy


urlpatterns= [
    path("", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("perfil/", views.perfil, name="perfil"),
    path("alterar-senha/", auth_views.PasswordChangeView.as_view(template_name="alterar_senha.html", success_url=reverse_lazy("perfil")), name="alterar_senha"),
    path("cadastro/", views.cadastro, name="cadastrar_usuario"),
    path("recuperar-senha/", auth_views.PasswordResetView.as_view(
        template_name="password_reset_form.html",
        email_template_name="password_reset_email.html",
        success_url=reverse_lazy("password_reset_done"),
    ), name="password_reset"),
    path("recuperar-senha/enviado/", auth_views.PasswordResetDoneView.as_view(
        template_name="password_reset_done.html",
    ), name="password_reset_done"),
    path("recuperar-senha/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="password_reset_confirm.html",
        success_url=reverse_lazy("password_reset_complete"),
    ), name="password_reset_confirm"),
    path("recuperar-senha/concluido/", auth_views.PasswordResetCompleteView.as_view(
        template_name="password_reset_complete.html",
    ), name="password_reset_complete"),
]