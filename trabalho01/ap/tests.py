from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.test.utils import override_settings

from .models import Categoria, Pedido, Servico
from .views import bad_request, error_page, permission_denied, server_error
from login.models import Perfil


class ErrorPageTests(TestCase):
    @override_settings(DEBUG=False)
    def test_unknown_url_uses_the_custom_not_found_page(self):
        response = self.client.get("/not-found-test/")

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Página não encontrada", status_code=404)
        self.assertContains(response, "error-cat", status_code=404)

    @override_settings(DEBUG=False)
    def test_server_error_uses_the_custom_page(self):
        response = Client(raise_request_exception=False).get("/error-test/")

        self.assertEqual(response.status_code, 500)
        self.assertContains(response, "Tivemos um imprevisto", status_code=500)

    def test_error_handlers_render_the_branded_page_with_the_correct_status(self):
        request = RequestFactory().get("/")
        handlers = (
            (bad_request, 400),
            (permission_denied, 403),
            (error_page, 404),
            (server_error, 500),
        )

        for handler, status_code in handlers:
            with self.subTest(status_code=status_code):
                response = handler(request)

                self.assertEqual(response.status_code, status_code)
                self.assertContains(response, str(status_code), status_code=status_code)
                self.assertContains(response, "/static/css/error.", status_code=status_code)
                self.assertContains(response, "error-cat", status_code=status_code)


class CompraLivroTests(TestCase):
    def setUp(self):
        self.livro = Servico.objects.create(
            nome='A biblioteca da meia-noite',
            descricao='Uma história sobre escolhas.',
            preco=Decimal('39.90'),
            estoque=2,
            categoria=Categoria.objects.create(nome='Ficção'),
        )
        self.usuario = User.objects.create_user(
            username='leitora',
            password='senha-forte-123',
        )

    def test_adicionar_livro_cria_item_na_sacola(self):
        response = self.client.post(
            reverse('adicionar_carrinho', args=[self.livro.id]),
            {'next': reverse('servicos')},
        )

        self.assertRedirects(response, reverse('servicos'))
        self.assertEqual(self.client.session['carrinho'], {str(self.livro.id): 1})

    def test_checkout_exige_login(self):
        self.client.post(reverse('adicionar_carrinho', args=[self.livro.id]))

        response = self.client.post(reverse('finalizar_pedido'))

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("finalizar_pedido")}',
        )
        self.assertFalse(Pedido.objects.exists())

    def test_sacola_exige_login(self):
        response = self.client.get(reverse("carrinho"))

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("carrinho")}',
        )

    def test_item_da_api_pode_ser_adicionado_e_removido_da_sacola(self):
        self.client.force_login(self.usuario)

        adicionar = self.client.post(
            reverse("adicionar_api_carrinho"),
            {
                "key": "openlibrary-item-1",
                "title": "Livro externo",
                "author": "Autora externa",
                "year": "2024",
                "image": "",
                "next": reverse("produtos"),
            },
        )
        self.assertRedirects(adicionar, reverse("produtos"))
        self.assertIn(
            "openlibrary-item-1",
            self.client.session["carrinho_api"],
        )

        sacola = self.client.get(reverse("carrinho"))
        self.assertContains(sacola, "Livro externo")
        self.assertContains(sacola, "R$ 20,00")
        remover = self.client.post(
            reverse("remover_api_carrinho", args=["openlibrary-item-1"]),
        )
        self.assertRedirects(remover, reverse("carrinho"))
        self.assertNotIn(
            "openlibrary-item-1",
            self.client.session["carrinho_api"],
        )

    def test_checkout_cria_pedido_e_reduz_estoque(self):
        self.client.force_login(self.usuario)
        self.client.post(reverse('adicionar_carrinho', args=[self.livro.id]))

        response = self.client.post(reverse('finalizar_pedido'))

        self.assertRedirects(response, reverse('pedidos'))
        pedido = Pedido.objects.get(usuario=self.usuario)
        self.assertEqual(pedido.total, Decimal('39.90'))
        self.assertEqual(pedido.itens.get().livro, self.livro)
        self.livro.refresh_from_db()
        self.assertEqual(self.livro.estoque, 1)
        self.assertEqual(self.client.session['carrinho'], {})


class VendedorTests(TestCase):
    def criar_vendedor(self, username):
        usuario = User.objects.create_user(username=username, password='senha-forte-123')
        Perfil.objects.create(usuario=usuario, tipo_usuario='vendedor')
        return usuario

    def test_cadastro_de_vendedor_cria_perfil_e_pode_acessar_formulario_de_livro(self):
        response = self.client.post(
            reverse("cadastrar_usuario"),
            {
                "username": "vendedor",
                "email": "vendedor@example.com",
                "tipo_usuario": "vendedor",
                "password1": "UmaSenha-Forte-987!",
                "password2": "UmaSenha-Forte-987!",
            },
        )

        self.assertRedirects(response, reverse("login"))
        usuario = User.objects.get(username="vendedor")
        self.assertEqual(Perfil.objects.get(usuario=usuario).tipo_usuario, "vendedor")
        self.client.force_login(usuario)
        self.assertEqual(self.client.get(reverse("addServico")).status_code, 200)

    def test_perfil_de_vendedor_pode_salvar_link_da_foto(self):
        vendedor = self.criar_vendedor("vendedora_foto")
        self.client.force_login(vendedor)
        foto = "https://example.com/foto-vendedora.jpg"

        response = self.client.post(reverse("perfil"), {
            "first_name": "Ana",
            "last_name": "Silva",
            "email": "ana@example.com",
            "foto_url": foto,
        })

        self.assertEqual(response.status_code, 200)
        vendedor.perfil.refresh_from_db()
        self.assertEqual(vendedor.perfil.foto_url, foto)

    def test_cliente_nao_pode_acessar_formulario_de_livro(self):
        cliente = User.objects.create_user(username='cliente', password='senha-forte-123')
        Perfil.objects.create(usuario=cliente, tipo_usuario='cliente')
        self.client.force_login(cliente)

        response = self.client.get(reverse("addServico"))

        self.assertEqual(response.status_code, 302)

    def test_vendedor_nao_edita_livro_de_outro_vendedor(self):
        vendedor_um = self.criar_vendedor('vendedor_um')
        vendedor_dois = self.criar_vendedor('vendedor_dois')
        livro = Servico.objects.create(
            nome='Livro protegido',
            preco=Decimal('25.00'),
            vendedor=vendedor_um,
        )
        self.client.force_login(vendedor_dois)

        editar = self.client.get(reverse("editarServico", args=[livro.id]))
        excluir = self.client.post(reverse("excluirServico", args=[livro.id]))

        self.assertEqual(editar.status_code, 404)
        self.assertEqual(excluir.status_code, 404)
        self.assertTrue(Servico.objects.filter(id=livro.id).exists())


class AdministradorTests(TestCase):
    def setUp(self):
        self.administrador = User.objects.create_user(
            username='administrador',
            password='senha-forte-123',
        )
        Perfil.objects.create(
            usuario=self.administrador,
            tipo_usuario='administrador',
        )
        self.vendedor = User.objects.create_user(
            username='vendedor',
            password='senha-forte-123',
        )
        Perfil.objects.create(
            usuario=self.vendedor,
            tipo_usuario='vendedor',
        )
        self.livro = Servico.objects.create(
            nome='Livro do vendedor',
            preco=Decimal('30.00'),
            vendedor=self.vendedor,
        )

    def test_administrador_pode_editar_e_excluir_livro_de_outro_vendedor(self):
        self.client.force_login(self.administrador)

        editar = self.client.get(reverse("editarServico", args=[self.livro.id]))
        excluir = self.client.post(reverse("excluirServico", args=[self.livro.id]))

        self.assertEqual(editar.status_code, 200)
        self.assertEqual(excluir.status_code, 302)
        self.assertFalse(Servico.objects.filter(id=self.livro.id).exists())

    def test_administrador_pode_excluir_vendedor(self):
        self.client.force_login(self.administrador)

        response = self.client.post(
            reverse("excluirVendedor", args=[self.vendedor.id]),
        )

        self.assertRedirects(response, reverse("integrantes"))
        self.assertFalse(User.objects.filter(id=self.vendedor.id).exists())

    def test_vendedor_aparece_na_lista_unica_de_integrantes(self):
        self.client.force_login(self.administrador)

        response = self.client.get(reverse("integrantes"))

        vendedores = [
            integrante for integrante in response.context["integrantes"]
            if integrante.get("vendedor")
        ]
        self.assertTrue(
            any(
                integrante["usuario_id"] == self.vendedor.id
                for integrante in vendedores
            )
        )

    def test_cliente_nao_acessa_contatos_nem_relatorios(self):
        cliente = User.objects.create_user(username="cliente_teste", password="senha-forte-123")
        Perfil.objects.create(usuario=cliente, tipo_usuario="cliente")
        self.client.force_login(cliente)

        self.assertEqual(self.client.get(reverse("contatos")).status_code, 302)
        self.assertEqual(self.client.get(reverse("relatorios")).status_code, 302)
        self.assertEqual(self.client.get(reverse("addIntegrante")).status_code, 302)

    def test_vendedor_nao_acessa_contatos_nem_relatorios(self):
        self.client.force_login(self.vendedor)

        self.assertEqual(self.client.get(reverse("contatos")).status_code, 302)
        self.assertEqual(self.client.get(reverse("relatorios")).status_code, 302)
        self.assertEqual(self.client.get(reverse("addIntegrante")).status_code, 302)

    def test_administrador_acessa_contatos_e_relatorios(self):
        self.client.force_login(self.administrador)

        self.assertEqual(self.client.get(reverse("contatos")).status_code, 200)
        self.assertEqual(self.client.get(reverse("relatorios")).status_code, 200)


class FiltrosEPaginacaoTests(TestCase):
    def setUp(self):
        self.cat_ficcao = Categoria.objects.create(nome="Ficção", ativo=True)
        self.cat_tecnologia = Categoria.objects.create(nome="Tecnologia", ativo=True)
        for i in range(1, 13):
            Servico.objects.create(
                nome=f"Livro Teste {i}",
                autor="Autor Alfa" if i % 2 == 0 else "Autor Beta",
                preco=Decimal(f"{i * 10}.00"),
                categoria=self.cat_ficcao if i <= 6 else self.cat_tecnologia,
                ativo=True,
                estoque=5,
            )

    def test_catalogo_filtra_por_nome_autor_categoria_e_preco(self):
        resp = self.client.get(reverse("servicos"), {"busca": "Teste 1"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Livro Teste 1")

        resp_autor = self.client.get(reverse("servicos"), {"autor": "Alfa"})
        self.assertEqual(resp_autor.status_code, 200)
        self.assertContains(resp_autor, "Autor Alfa")

        resp_cat = self.client.get(reverse("servicos"), {"categoria": self.cat_tecnologia.id})
        self.assertEqual(resp_cat.status_code, 200)
        self.assertContains(resp_cat, "Livro Teste 7")

        resp_preco = self.client.get(reverse("servicos"), {"preco": "baixo"})
        self.assertEqual(resp_preco.status_code, 200)

    def test_catalogo_paginacao(self):
        resp_p1 = self.client.get(reverse("servicos"), {"page": "1"})
        self.assertEqual(resp_p1.status_code, 200)
        self.assertEqual(len(resp_p1.context["livros"]), 8)

        resp_p2 = self.client.get(reverse("servicos"), {"page": "2"})
        self.assertEqual(resp_p2.status_code, 200)
        self.assertEqual(len(resp_p2.context["livros"]), 4)

    def test_produtos_paginacao_e_filtros(self):
        resp = self.client.get(reverse("produtos"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("produtos_api", resp.context)
        self.assertIn("page_local", resp.context)
        self.assertIn("paginator_local", resp.context)

        resp_local = self.client.get(reverse("produtos"), {"busca": "Teste 2", "autor": "Alfa"})
        self.assertEqual(resp_local.status_code, 200)
        self.assertContains(resp_local, "Livro Teste 2")

        resp_p1 = self.client.get(reverse("produtos"), {"page_local": "1"})
        self.assertEqual(resp_p1.status_code, 200)
        self.assertEqual(len(resp_p1.context["livros"]), 6)

