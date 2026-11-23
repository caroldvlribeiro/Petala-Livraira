from django.urls import path 
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("livros/", views.servicos, name="servicos"),
    path("servicos", views.servicos, name="servicos"),
    path("add-servico", views.addServico, name="addServico"),
    path("excluir-servico/<int:id>", views.excluirServico, name="excluirServico"),
    path("editar-servico/<int:id>", views.editarServico, name="editarServico"),
    path("produtos", views.produtos, name="produtos"),
    path("sacola/", views.carrinho, name="carrinho"),
    path("sacola/adicionar/<int:id>/", views.adicionar_carrinho, name="adicionar_carrinho"),
    path("sacola/adicionar-api/", views.adicionar_api_carrinho, name="adicionar_api_carrinho"),
    path("sacola/remover/<int:id>/", views.remover_carrinho, name="remover_carrinho"),
    path("sacola/remover-api/<str:key>/", views.remover_api_carrinho, name="remover_api_carrinho"),
    path("pedidos/finalizar/", views.finalizar_pedido, name="finalizar_pedido"),
    path("meus-pedidos/", views.pedidos, name="pedidos"),
    path("novo-contato", views.novoContato, name="novoContato"),
    path("contatos", views.contatos, name="contatos"),
    path("excluir-contato/<int:id>", views.excluirContato, name="excluirContato"),
    path("integrantes",views.integrantes, name="integrantes"),
    path("add-integrante", views.addIntegrante, name="addIntegrante"),
    path("editar-integrante/<int:id>", views.editarIntegrante, name="editarIntegrante"),
    path("del-integrante/<int:id>", views.delIntegrante, name="delIntegrante"),
    path("excluir-vendedor/<int:id>", views.excluirVendedor, name="excluirVendedor"),
    
    path("categoria-api/", views.categorias_api, name="categorias_api"),
    path("categoria-api/<int:id>", views.categoria_api, name="categoria_api"),
    path("relatorios/",views.relatorios, name='relatorios'),
]
