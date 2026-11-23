from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from ap.models import Categoria, Contato, Pedido, Servico
from ap.supabase_sync import (
    sincronizar_categoria,
    sincronizar_contato,
    sincronizar_livro,
    sincronizar_pedido,
    sincronizar_perfil,
)


class Command(BaseCommand):
    help = "Sincroniza os dados existentes do Django com o Supabase."

    def handle(self, *args, **options):
        contadores = {
            "perfis": 0,
            "categorias": 0,
            "livros": 0,
            "contatos": 0,
            "pedidos": 0,
        }

        for usuario in User.objects.select_related("perfil").all():
            perfil = getattr(usuario, "perfil", None)
            if perfil is not None and sincronizar_perfil(usuario, perfil):
                contadores["perfis"] += 1
        for categoria in Categoria.objects.all():
            if sincronizar_categoria(categoria):
                contadores["categorias"] += 1
        for livro in Servico.objects.select_related("categoria", "vendedor").all():
            if sincronizar_livro(livro):
                contadores["livros"] += 1
        for contato in Contato.objects.all():
            if sincronizar_contato(contato):
                contadores["contatos"] += 1
        for pedido in Pedido.objects.prefetch_related("itens").all():
            if sincronizar_pedido(pedido):
                contadores["pedidos"] += 1

        self.stdout.write(self.style.SUCCESS(
            "Sincronização concluída: "
            + ", ".join(f"{nome}={quantidade}" for nome, quantidade in contadores.items())
        ))
