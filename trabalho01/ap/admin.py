from django.contrib import admin
from .models import Categoria, Contato, ItemPedido, Pedido, Servico


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "descricao")
    ordering = ("nome",)
    list_per_page = 25


@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    list_display = ("nome", "email", "telefone")
    search_fields = ("nome", "email", "telefone", "mensagem")
    ordering = ("nome",)
    readonly_fields = ("nome", "email", "telefone", "mensagem")
    list_per_page = 25


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ("nome", "autor", "categoria", "preco", "estoque", "ativo", "criado_em")
    list_filter = ("categoria", "ativo")
    search_fields = ("nome", "autor", "isbn", "descricao", "categoria__nome")
    ordering = ("nome", "preco")
    date_hierarchy = "criado_em"
    readonly_fields = ("criado_em", "atualizado_em")
    list_per_page = 25


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "status", "total", "criado_em")
    list_filter = ("status", "criado_em")
    search_fields = ("usuario__username", "usuario__email")
    readonly_fields = ("criado_em",)


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "livro", "quantidade", "preco_unitario")
    search_fields = ("livro__nome", "pedido__usuario__username")
