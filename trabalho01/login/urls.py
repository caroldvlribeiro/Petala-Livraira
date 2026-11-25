from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.CustomLoginView.as_view(), name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("perfil/", views.perfil, name="perfil"),
    path("alterar-senha/", views.CustomPasswordChangeView.as_view(), name="alterar_senha"),
    path("cadastro/", views.cadastro, name="cadastrar_usuario"),
    path("recuperar-senha/", views.CustomPasswordResetView.as_view(), name="password_reset"),
    path("recuperar-senha/enviado/", auth_views.PasswordResetDoneView.as_view(
        template_name="password_reset_done.html",
    ), name="password_reset_done"),
    path("recuperar-senha/<uidb64>/<token>/", views.CustomPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("recuperar-senha/concluido/", auth_views.PasswordResetCompleteView.as_view(
        template_name="password_reset_complete.html",
    ), name="password_reset_complete"),
]
