import logging

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import (
    CadastroForm,
    CustomPasswordChangeForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
    LoginForm,
)
from .models import Perfil
from ap.supabase_client import supabase
from ap.supabase_sync import remover_perfil, sincronizar_perfil

logger = logging.getLogger(__name__)


class CustomLoginView(auth_views.LoginView):
    template_name = "login.html"
    authentication_form = LoginForm

    def form_valid(self, form):
        user = form.get_user()
        nome = user.first_name or user.username
        messages.success(self.request, f"Olá, {nome}! Bem-vindo(a) de volta à Pétala Livraria.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Nome de usuário ou senha incorretos. Por favor, tente novamente.")
        return super().form_invalid(form)


class CustomLogoutView(auth_views.LogoutView):
    def post(self, request, *args, **kwargs):
        messages.info(request, "Você encerrou sua sessão com sucesso. Até logo!")
        return super().post(request, *args, **kwargs)


class CustomPasswordChangeView(SuccessMessageMixin, auth_views.PasswordChangeView):
    template_name = "alterar_senha.html"
    form_class = CustomPasswordChangeForm
    success_url = reverse_lazy("perfil")
    success_message = "Sua senha foi alterada com sucesso!"

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível alterar a senha. Confira as orientações nos campos abaixo.")
        return super().form_invalid(form)


class CustomPasswordResetView(SuccessMessageMixin, auth_views.PasswordResetView):
    template_name = "password_reset_form.html"
    email_template_name = "password_reset_email.html"
    subject_template_name = "password_reset_subject.txt"
    form_class = CustomPasswordResetForm
    success_url = reverse_lazy("password_reset_done")
    success_message = "Solicitação enviada. Verifique as instruções enviadas para o seu e-mail."

    def extra_email_context_value(self):
        from django.conf import settings
        domain = getattr(settings, "SITE_DOMAIN", "petala-livraria.onrender.com")
        protocol = getattr(settings, "SITE_PROTOCOL", "https")
        if self.request:
            # If not localhost, can use host, otherwise preference goes to configured SITE_DOMAIN
            req_host = self.request.get_host()
            if req_host and not any(h in req_host for h in ("127.0.0.1", "localhost")):
                domain = req_host
            if self.request.is_secure():
                protocol = "https"
        return {"domain": domain, "protocol": protocol}

    def form_valid(self, form):
        opts = {
            "use_https": getattr(self.request, "is_secure", lambda: True)(),
            "token_generator": self.token_generator,
            "from_email": self.from_email,
            "email_template_name": self.email_template_name,
            "subject_template_name": self.subject_template_name,
            "request": self.request,
            "html_email_template_name": self.html_email_template_name,
            "extra_email_context": self.extra_email_context_value(),
        }
        try:
            form.save(**opts)
            # Imprime o link diretamente no console do Render sem quebras quoted-printable
            for user in form.get_users(form.cleaned_data.get("email")):
                from django.contrib.auth.tokens import default_token_generator
                from django.utils.http import urlsafe_base64_encode
                from django.utils.encoding import force_bytes
                from django.urls import reverse
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                tok = default_token_generator.make_token(user)
                direct_url = f"https://petala-livraria.onrender.com/login/recuperar-senha/{uid}/{tok}/"
                print(f"\n========================================\n[LINK DE RECUPERACAO - SEM QUEBRA]:\n{direct_url}\n========================================\n", flush=True)
            logger.info("E-mail de recuperação de senha processado para %s", form.cleaned_data.get("email"))
        except Exception as exc:
            logger.exception("Falha crítica ao enviar e-mail de recuperação de senha: %s", exc)
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, "Informe um endereço de e-mail válido para recuperar o acesso.")
        return super().form_invalid(form)


class CustomPasswordResetConfirmView(SuccessMessageMixin, auth_views.PasswordResetConfirmView):
    template_name = "password_reset_confirm.html"
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy("password_reset_complete")
    success_message = "Sua nova senha foi gravada com sucesso! Você já pode entrar com a nova credencial."

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível redefinir sua senha. Verifique as instruções abaixo.")
        return super().form_invalid(form)


@login_required
def dashboard(request):
    perfil, _ = Perfil.objects.get_or_create(
        usuario=request.user,
        defaults={"tipo_usuario": "cliente"},
    )
    return render(request, "dashboard.html")


@login_required
def perfil(request):
    usuario = request.user
    perfil_obj, _ = Perfil.objects.get_or_create(usuario=usuario)

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()

        if not email:
            messages.error(request, "O campo de e-mail não pode ficar em branco.")
            return render(request, "perfil.html", {"usuario": usuario})

        usuario.first_name = first_name
        usuario.last_name = last_name
        usuario.email = email
        usuario.save()

        if perfil_obj.tipo_usuario == "vendedor":
            foto_url = request.POST.get("foto_url", "").strip()
            perfil_obj.foto_url = foto_url
            perfil_obj.save(update_fields=["foto_url"])
            if supabase is not None:
                try:
                    nome = usuario.get_full_name() or usuario.username
                    supabase.table("integrantes").update({
                        "foto_url": perfil_obj.foto_url,
                    }).eq("nome", nome).execute()
                except Exception:
                    logger.exception("Não foi possível atualizar a foto do vendedor no Supabase.")

        sincronizar_perfil(usuario, perfil_obj)
        messages.success(request, "Seus dados de perfil foram atualizados com sucesso!")
        return render(request, "perfil.html", {"usuario": usuario, "mensagem": "Perfil atualizado com sucesso!"})

    return render(request, "perfil.html", {"usuario": usuario})


def cadastro(request):
    if request.method == "POST":
        form = CadastroForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                usuario = form.save()
                tipo_usuario = form.cleaned_data.get("tipo_usuario") or "cliente"
                perfil = Perfil.objects.create(
                    usuario=usuario,
                    tipo_usuario=tipo_usuario,
                    foto_url=form.cleaned_data.get("foto_url") if tipo_usuario == "vendedor" else "",
                )
                sincronizar_perfil(usuario, perfil)
                if tipo_usuario == "vendedor" and supabase is not None:
                    try:
                        supabase.table("integrantes").insert({
                            "nome": usuario.get_full_name() or usuario.username,
                            "cargo": "Vendedor",
                            "biografia": "Vendedor parceiro da Pétala Livraria.",
                            "foto_url": perfil.foto_url,
                        }).execute()
                    except Exception:
                        logger.exception("Não foi possível cadastrar o vendedor na equipe do Supabase.")
                        messages.warning(
                            request,
                            "Sua conta foi criada, mas o perfil de integrante será sincronizado assim que o Supabase estiver disponível.",
                        )
            messages.success(request, "Usuário cadastrado com sucesso! Você já pode entrar.")
            return redirect("login")
        else:
            messages.error(request, "Não foi possível concluir o cadastro. Verifique os campos com erro abaixo.")
    else:
        form = CadastroForm()

    return render(request, "cadastro.html", {"form": form})
