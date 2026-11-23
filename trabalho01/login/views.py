from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
import logging

from .forms import CadastroForm
from .models import Perfil
from ap.supabase_client import supabase
from ap.supabase_sync import remover_perfil, sincronizar_perfil

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    perfil, _ = Perfil.objects.get_or_create(
        usuario=request.user,
        defaults={"tipo_usuario": "cliente"},
    )

    return render(request, "dashboard.html")

@login_required
def perfil(request):
    if request.method == "POST":
        # Aqui você pode adicionar a lógica para atualizar o perfil do usuário
        usuario = request.user
        usuario.first_name = request.POST.get("first_name", usuario.first_name)
        usuario.last_name = request.POST.get("last_name", usuario.last_name)
        usuario.email = request.POST.get("email", usuario.email)
        usuario.save()
        perfil, _ = Perfil.objects.get_or_create(usuario=usuario)
        if perfil.tipo_usuario == "vendedor":
            perfil.foto_url = request.POST.get("foto_url", perfil.foto_url)
            perfil.save(update_fields=["foto_url"])
            if supabase is not None:
                try:
                    nome = usuario.get_full_name() or usuario.username
                    supabase.table("integrantes").update({
                        "foto_url": perfil.foto_url,
                    }).eq("nome", nome).execute()
                except Exception:
                    logger.exception("Não foi possível atualizar a foto do vendedor no Supabase.")
        sincronizar_perfil(usuario, perfil)
        
        return render(request, "perfil.html", {"mensagem": "Perfil atualizado com sucesso!"})
   
    return render(request, "perfil.html", {"usuario": request.user})

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
                            "Sua conta foi criada, mas o perfil de integrante será sincronizado quando o Supabase estiver disponível.",
                        )
            messages.success(request, "Usuário cadastrado com sucesso! Você já pode entrar.")
            return redirect("login")
    else:
        form = CadastroForm()

    return render(request, "cadastro.html", {"form": form})