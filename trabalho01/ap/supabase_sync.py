import logging
import os
from pathlib import Path

from .supabase_client import supabase


logger = logging.getLogger(__name__)


def _execute(operation, descricao):
    if supabase is None:
        return False
    try:
        operation()
        return True
    except Exception as exc:
        logger.exception("Falha ao sincronizar %s no Supabase.", descricao)
        return False


def upload_imagem_storage(livro):
    if supabase is None or not livro.imagem:
        return None
    try:
        nome_arquivo = f"capas/{livro.id}_{Path(livro.imagem.name).name}"
        dados = None
        caminho_local = getattr(livro.imagem, "path", None)
        if caminho_local and os.path.exists(caminho_local):
            with open(caminho_local, "rb") as f:
                dados = f.read()
        elif hasattr(livro.imagem, "open"):
            try:
                livro.imagem.open("rb")
                dados = livro.imagem.read()
            except Exception:
                pass
            finally:
                if hasattr(livro.imagem, "close"):
                    livro.imagem.close()

        if dados:
            supabase.storage.from_("livros").upload(
                path=nome_arquivo,
                file=dados,
                file_options={"upsert": "true"}
            )
            return supabase.storage.from_("livros").get_public_url(nome_arquivo)
    except Exception as exc:
        logger.warning("Falha ao enviar capa para o Supabase Storage: %s", exc)
    return None


def sincronizar_perfil(usuario, perfil):
    def salvar():
        supabase.table("perfis").upsert({
            "django_id": usuario.id,
            "username": usuario.username,
            "nome": usuario.first_name,
            "sobrenome": usuario.last_name,
            "email": usuario.email,
            "tipo_usuario": perfil.tipo_usuario,
            "foto_url": perfil.foto_url,
        }, on_conflict="django_id").execute()

    return _execute(salvar, "perfil")


def remover_perfil(usuario_id):
    def remover():
        supabase.table("perfis").delete().eq("django_id", usuario_id).execute()

    return _execute(remover, "perfil")


def sincronizar_categoria(categoria):
    def salvar():
        supabase.table("categorias").upsert({
            "django_id": categoria.id,
            "nome": categoria.nome,
            "descricao": categoria.descricao,
            "ativo": categoria.ativo,
        }, on_conflict="django_id").execute()

    return _execute(salvar, "categoria")


def remover_categoria(categoria_id):
    def remover():
        supabase.table("categorias").delete().eq("django_id", categoria_id).execute()

    return _execute(remover, "categoria")


def sincronizar_livro(livro):
    def salvar():
        url_imagem = upload_imagem_storage(livro) or (livro.imagem.url if livro.imagem else None)
        supabase.table("livros").upsert({
            "django_id": livro.id,
            "nome": livro.nome,
            "descricao": livro.descricao,
            "preco": str(livro.preco),
            "imagem": url_imagem,
            "autor": livro.autor,
            "isbn": livro.isbn,
            "estoque": livro.estoque,
            "ativo": livro.ativo,
            "categoria_id": livro.categoria_id,
            "vendedor_id": livro.vendedor_id,
        }, on_conflict="django_id").execute()

    return _execute(salvar, "livro")


def remover_livro(livro_id):
    def remover():
        supabase.table("livros").delete().eq("django_id", livro_id).execute()

    return _execute(remover, "livro")


def sincronizar_contato(contato):
    def salvar():
        supabase.table("contatos").upsert({
            "django_id": contato.id,
            "nome": contato.nome,
            "email": contato.email,
            "telefone": contato.telefone,
            "mensagem": contato.mensagem,
        }, on_conflict="django_id").execute()

    return _execute(salvar, "contato")


def remover_contato(contato_id):
    def remover():
        supabase.table("contatos").delete().eq("django_id", contato_id).execute()

    return _execute(remover, "contato")


def sincronizar_pedido(pedido):
    def salvar():
        supabase.table("pedidos").upsert({
            "django_id": pedido.id,
            "usuario_id": pedido.usuario_id,
            "status": pedido.status,
            "total": str(pedido.total),
            "criado_em": pedido.criado_em.isoformat(),
        }, on_conflict="django_id").execute()
        for item in pedido.itens.select_related("livro").all():
            supabase.table("itens_pedido").upsert({
                "django_id": item.id,
                "pedido_id": item.pedido_id,
                "livro_id": item.livro_id,
                "quantidade": item.quantidade,
                "preco_unitario": str(item.preco_unitario),
            }, on_conflict="django_id").execute()

    return _execute(salvar, "pedido")


def sincronizar_carrinho(usuario, carrinho):
    def salvar():
        supabase.table("carrinhos").upsert({
            "usuario_id": usuario.id,
            "itens": carrinho,
        }, on_conflict="usuario_id").execute()

    return _execute(salvar, "carrinho")


def remover_carrinho(usuario_id):
    def remover():
        supabase.table("carrinhos").delete().eq("usuario_id", usuario_id).execute()

    return _execute(remover, "carrinho")
