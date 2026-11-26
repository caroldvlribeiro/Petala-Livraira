from decimal import Decimal
import hashlib
import logging

from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models.aggregates import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .serializers import CategoriaSerializer
from .models import Contato, ItemPedido, Pedido, Servico, Categoria
from .forms import FormContato, FormServico
from .supabase_client import supabase
from .supabase_sync import (
    remover_categoria,
    remover_contato,
    remover_livro,
    remover_perfil,
    sincronizar_categoria,
    sincronizar_carrinho,
    remover_carrinho as remover_carrinho_supabase,
    sincronizar_contato,
    sincronizar_livro,
    sincronizar_pedido,
)
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
import requests

logger = logging.getLogger(__name__)


def can_manage_catalog(user):
    if not user.is_authenticated or not user.is_active:
        return False
    perfil = getattr(user, "perfil", None)
    return user.is_staff or (perfil is not None and perfil.tipo_usuario in ("vendedor", "administrador"))


def staff_required(view):
    return user_passes_test(can_manage_catalog)(view)


def admin_required(view):
    def is_administrator(user):
        if not user.is_authenticated or not user.is_active:
            return False
        perfil = getattr(user, "perfil", None)
        return user.is_staff or (perfil is not None and perfil.tipo_usuario == "administrador")

    return user_passes_test(is_administrator)(view)


def is_administrator(user):
    if not user.is_authenticated or not user.is_active:
        return False
    perfil = getattr(user, "perfil", None)
    return user.is_staff or (perfil is not None and perfil.tipo_usuario == "administrador")

# Create your views here.

from django.http import Http404

from django.shortcuts import render
from django.http import Http404, HttpResponseServerError

# Custom error page view
def error_page(request, exception=None):
    # Use the new error template
    return render(request, "error.html", status=404)

# Deliberate error view for testing
def deliberate_error(request):
    raise RuntimeError("Deliberate failure for testing error handling")

def index(request):
    livros = Servico.objects.filter(ativo=True).order_by('-criado_em')[:4]
    return render(request, "index.html", {'livros_destaque': livros})

def servicos(request):
    servicos = Servico.objects.filter(ativo=True).exclude(preco=0)
    
    total_catalogo = servicos.count()
    tem_servicos = servicos.exists()
    
    mais_barato = servicos.order_by('preco').first()
    mais_caro = servicos.order_by('-preco').first()
    
    # Filtro por Nome (título ou palavra-chave)
    busca = request.GET.get('busca', '').strip()
    if busca:
        servicos = servicos.filter(nome__icontains=busca)
        
    # Filtro por Autor
    autor = request.GET.get('autor', '').strip()
    if autor:
        servicos = servicos.filter(autor__icontains=autor)

    # Filtro por Categoria
    categorias = Categoria.objects.filter(ativo=True)
    categoria = request.GET.get('categoria', '').strip()
    if categoria:
        servicos = servicos.filter(categoria_id=categoria)
        
    # Filtro por Faixa de Preço
    preco = request.GET.get('preco', '').strip()
    if preco == 'baixo':
        servicos = servicos.filter(preco__lte=50)
    elif preco == 'medio':
        servicos = servicos.filter(preco__gt=50, preco__lte=250)
    elif preco == 'alto':
        servicos = servicos.filter(preco__gt=250)
    
    # Ordenação
    ordem = request.GET.get('ordem', '').strip()
    if ordem == 'menor':
        servicos = servicos.order_by('preco')
    elif ordem == 'maior':
        servicos = servicos.order_by('-preco')
    elif ordem == 'nome':
        servicos = servicos.order_by('nome')
    else:
        servicos = servicos.order_by('-criado_em')

    total_filtrados = servicos.count()

    # Paginação (8 livros por página)
    paginator = Paginator(servicos, 8)
    page_number = request.GET.get('page', 1)
    try:
        livros_page = paginator.page(page_number)
    except PageNotAnInteger:
        livros_page = paginator.page(1)
    except EmptyPage:
        livros_page = paginator.page(paginator.num_pages)

    # Parâmetros de query mantendo filtros na paginação
    params = request.GET.copy()
    if 'page' in params:
        del params['page']
    filtros_query = params.urlencode()

    contexto = {
        'servicos': livros_page,
        'livros': livros_page,
        'page_obj': livros_page,
        'paginator': paginator,
        'total_servicos': total_filtrados,
        'total_catalogo': total_catalogo,
        'tem_servicos': tem_servicos,
        'mais_barato': mais_barato,
        'mais_caro': mais_caro,
        'busca': busca,
        'autor': autor,
        'categoria': categoria,
        'categorias': categorias,
        'preco': preco,
        'ordem': ordem,
        'filtros_query': filtros_query,
    }
    return render(request, "servicos.html", contexto)

@staff_required
def addServico(request):
    form = FormServico(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            livro = form.save(commit=False)
            livro.vendedor = request.user
            livro.save()
            sincronizar_livro(livro)
            messages.success(request, f'Livro "{livro.nome}" cadastrado com sucesso no catálogo!')
            return redirect('servicos')
        else:
            messages.error(request, "Não foi possível cadastrar o livro. Verifique os campos destacados abaixo.")

    return render (request, "add-servico.html", {'form': form})

@staff_required
def excluirServico(request, id):
    if is_administrator(request.user):
        servico = get_object_or_404(Servico, id=id)
    else:
        servico = get_object_or_404(Servico, id=id, vendedor=request.user)
    if request.method == 'POST':
        nome_livro = servico.nome
        if servico.imagem:
            servico.imagem.delete(save=False)
        servico_id = servico.id
        servico.delete()
        remover_livro(servico_id)
        messages.success(request, f'O livro "{nome_livro}" foi excluído com sucesso.')
    return redirect('servicos')

@staff_required
def editarServico(request, id):
    if is_administrator(request.user):
        servico = get_object_or_404(Servico, id=id)
    else:
        servico = get_object_or_404(Servico, id=id, vendedor=request.user)
    form = FormServico(request.POST or None, request.FILES or None, instance=servico)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            sincronizar_livro(servico)
            messages.success(request, f'As alterações do livro "{servico.nome}" foram salvas com sucesso!')
            return redirect('servicos')
        else:
            messages.error(request, "Não foi possível atualizar o livro. Corrija os erros apontados no formulário.")

    return render(request, "editar-servico.html", {'form': form, 'livro': servico})

def produtos(request):
    produtos_api = cache.get('openlibrary_produtos')
    api_erro = None

    if not produtos_api:
        produtos_api = []
        try:
            headers = {
                'User-Agent': 'PetalaLivraria/1.0 (https://petala.sa-east-1.elasticbeanstalk.com; contato@petala.com.br)'
            }
            resposta = requests.get(
                'https://openlibrary.org/search.json',
                params={'q': 'literatura brasileira', 'limit': 36},
                headers=headers,
                timeout=10,
            )
            resposta.raise_for_status()
            for item in resposta.json().get('docs', []):
                capa = item.get('cover_i')
                produtos_api.append({
                    'key': hashlib.sha1(
                        f"{item.get('title', 'Livro sem título')}|{(item.get('author_name') or ['Autor desconhecido'])[0]}|{item.get('first_publish_year') or ''}".encode("utf-8")
                    ).hexdigest(),
                    'title': item.get('title', 'Livro sem título'),
                    'author': (item.get('author_name') or ['Autor desconhecido'])[0],
                    'year': item.get('first_publish_year'),
                    'image': f'https://covers.openlibrary.org/b/id/{capa}-M.jpg' if capa else '',
                })
            if produtos_api:
                cache.set('openlibrary_produtos', produtos_api, 1800)
        except (requests.RequestException, ValueError) as e:
            logger.warning("Falha ao consultar API da Open Library: %s", e)
            produtos_api = [
                {
                    'key': 'fallback-dom-casmurro',
                    'title': 'Dom Casmurro',
                    'author': 'Machado de Assis',
                    'year': 1899,
                    'image': 'https://covers.openlibrary.org/b/id/8231856-M.jpg',
                },
                {
                    'key': 'fallback-memorias-postumas',
                    'title': 'Memórias Póstumas de Brás Cubas',
                    'author': 'Machado de Assis',
                    'year': 1881,
                    'image': 'https://covers.openlibrary.org/b/id/11153244-M.jpg',
                },
                {
                    'key': 'fallback-grande-sertao',
                    'title': 'Grande Sertão: Veredas',
                    'author': 'João Guimarães Rosa',
                    'year': 1956,
                    'image': 'https://covers.openlibrary.org/b/id/12818862-M.jpg',
                },
                {
                    'key': 'fallback-hora-da-estrela',
                    'title': 'A Hora da Estrela',
                    'author': 'Clarice Lispector',
                    'year': 1977,
                    'image': 'https://covers.openlibrary.org/b/id/8314126-M.jpg',
                },
                {
                    'key': 'fallback-capitaes-da-areia',
                    'title': 'Capitães da Areia',
                    'author': 'Jorge Amado',
                    'year': 1937,
                    'image': 'https://covers.openlibrary.org/b/id/8743232-M.jpg',
                },
                {
                    'key': 'fallback-quarto-de-despejo',
                    'title': 'Quarto de Despejo',
                    'author': 'Carolina Maria de Jesus',
                    'year': 1960,
                    'image': 'https://covers.openlibrary.org/b/id/10543210-M.jpg',
                },
            ]

    # Filtro opcional na API por busca (título ou autor)
    busca_api = request.GET.get('busca_api', '').strip()
    if busca_api:
        termo = busca_api.lower()
        produtos_api_filtrados = [
            item for item in produtos_api
            if termo in item.get('title', '').lower() or termo in item.get('author', '').lower()
        ]
    else:
        produtos_api_filtrados = produtos_api

    # Paginação dos livros da API (6 por página)
    paginator_api = Paginator(produtos_api_filtrados, 6)
    page_api_num = request.GET.get('page_api', 1)
    try:
        produtos_api_page = paginator_api.page(page_api_num)
    except PageNotAnInteger:
        produtos_api_page = paginator_api.page(1)
    except EmptyPage:
        produtos_api_page = paginator_api.page(paginator_api.num_pages)

    # Livros próprios do sistema (Estante local)
    livros_queryset = Servico.objects.filter(ativo=True)

    # Filtros na Estante Local (Nome, Autor, Categoria, Preço)
    busca = request.GET.get('busca', '').strip()
    if busca:
        livros_queryset = livros_queryset.filter(nome__icontains=busca)

    autor = request.GET.get('autor', '').strip()
    if autor:
        livros_queryset = livros_queryset.filter(autor__icontains=autor)

    categorias = Categoria.objects.filter(ativo=True)
    categoria = request.GET.get('categoria', '').strip()
    if categoria:
        livros_queryset = livros_queryset.filter(categoria_id=categoria)

    preco = request.GET.get('preco', '').strip()
    if preco == 'baixo':
        livros_queryset = livros_queryset.filter(preco__lte=50)
    elif preco == 'medio':
        livros_queryset = livros_queryset.filter(preco__gt=50, preco__lte=250)
    elif preco == 'alto':
        livros_queryset = livros_queryset.filter(preco__gt=250)

    # Paginação dos livros locais (6 por página)
    paginator_local = Paginator(livros_queryset.order_by('-criado_em'), 6)
    page_local_num = request.GET.get('page_local', 1)
    try:
        livros_local_page = paginator_local.page(page_local_num)
    except PageNotAnInteger:
        livros_local_page = paginator_local.page(1)
    except EmptyPage:
        livros_local_page = paginator_local.page(paginator_local.num_pages)

    # Preservar parâmetros de query nos links de paginação
    params_api = request.GET.copy()
    if 'page_api' in params_api:
        del params_api['page_api']
    query_api = params_api.urlencode()

    params_local = request.GET.copy()
    if 'page_local' in params_local:
        del params_local['page_local']
    query_local = params_local.urlencode()

    return render(request, "produtos.html", {
        'produtos_api': produtos_api_page,
        'page_api': produtos_api_page,
        'paginator_api': paginator_api,
        'query_api': query_api,
        'busca_api': busca_api,
        'total_api': len(produtos_api_filtrados),

        'livros': livros_local_page,
        'page_local': livros_local_page,
        'paginator_local': paginator_local,
        'query_local': query_local,
        'total_local': livros_queryset.count(),

        'categorias': categorias,
        'categoria': categoria,
        'busca': busca,
        'autor': autor,
        'preco': preco,
        'api_erro': api_erro,
    })


def _carrinho(request):
    return request.session.setdefault('carrinho', {})


@login_required
def carrinho(request):
    itens = []
    itens_api = []
    total = Decimal('0.00')
    for livro_id, quantidade in _carrinho(request).items():
        livro = Servico.objects.filter(id=livro_id, ativo=True).first()
        if not livro:
            continue
        quantidade = min(int(quantidade), livro.estoque)
        if quantidade < 1:
            continue
        subtotal = livro.preco * quantidade
        itens.append({'livro': livro, 'quantidade': quantidade, 'subtotal': subtotal})
        total += subtotal
    for item in request.session.setdefault('carrinho_api', {}).values():
        quantidade = int(item.get('quantidade', 1))
        preco = Decimal(item.get('preco') or '20.00')
        subtotal = preco * quantidade
        itens_api.append({
            'key': item['key'],
            'title': item['title'],
            'author': item['author'],
            'year': item['year'],
            'image': item['image'],
            'preco': preco,
            'subtotal': subtotal,
            'quantidade': quantidade,
        })
        total += subtotal
    return render(request, 'carrinho.html', {
        'itens': itens,
        'itens_api': itens_api,
        'total': total,
    })


def adicionar_carrinho(request, id):
    if request.method != 'POST':
        return redirect('produtos')
    livro = get_object_or_404(Servico, id=id, ativo=True)
    carrinho = _carrinho(request)
    atual = int(carrinho.get(str(id), 0))
    if atual < livro.estoque:
        carrinho[str(id)] = atual + 1
        request.session.modified = True
        if request.user.is_authenticated:
            sincronizar_carrinho(request.user, {
                'local': carrinho,
                'api': request.session.setdefault('carrinho_api', {}),
            })
        messages.success(request, f'{livro.nome} foi adicionado à sacola.')
    else:
        messages.warning(request, 'Não há mais exemplares disponíveis desse livro.')
    return redirect(request.POST.get('next') or 'produtos')


@login_required
def adicionar_api_carrinho(request):
    if request.method != 'POST':
        return redirect('produtos')

    item_key = request.POST.get('key', '')
    title = request.POST.get('title', '').strip()
    if not item_key or not title:
        messages.warning(request, 'Não foi possível adicionar esta recomendação à sacola.')
        return redirect('produtos')

    carrinho_api = request.session.setdefault('carrinho_api', {})
    atual = carrinho_api.get(item_key)
    if atual:
        atual['quantidade'] = int(atual.get('quantidade', 1)) + 1
    else:
        carrinho_api[item_key] = {
            'key': item_key,
            'title': title,
            'author': request.POST.get('author', 'Autor desconhecido'),
            'year': request.POST.get('year', ''),
            'image': request.POST.get('image', ''),
            'preco': '20.00',
            'quantidade': 1,
        }
    request.session.modified = True
    if request.user.is_authenticated:
        sincronizar_carrinho(request.user, {
            'local': _carrinho(request),
            'api': carrinho_api,
        })
    messages.success(request, f'{title} foi adicionado à sacola.')
    return redirect(request.POST.get('next') or 'produtos')


def remover_carrinho(request, id):
    if request.method == 'POST':
        carrinho = _carrinho(request)
        removido = carrinho.pop(str(id), None)
        request.session.modified = True
        if request.user.is_authenticated:
            sincronizar_carrinho(request.user, {
                'local': carrinho,
                'api': request.session.setdefault('carrinho_api', {}),
            })
        if removido is not None:
            messages.success(request, 'Item removido da sacola com sucesso.')
    return redirect('carrinho')


@login_required
def remover_api_carrinho(request, key):
    if request.method == 'POST':
        carrinho_api = request.session.setdefault('carrinho_api', {})
        removido = carrinho_api.pop(key, None)
        request.session.modified = True
        sincronizar_carrinho(request.user, {
            'local': _carrinho(request),
            'api': carrinho_api,
        })
        if removido is not None:
            messages.success(request, 'Recomendação externa removida da sacola.')
    return redirect('carrinho')


@login_required
@transaction.atomic
def finalizar_pedido(request):
    if request.method != 'POST':
        return redirect('carrinho')
    carrinho = _carrinho(request)
    if not carrinho:
        messages.warning(request, 'Sua sacola está vazia.')
        return redirect('carrinho')
    pedido = Pedido.objects.create(usuario=request.user)
    total = Decimal('0.00')
    for livro_id, quantidade in carrinho.items():
        livro = Servico.objects.select_for_update().filter(id=livro_id, ativo=True).first()
        quantidade = int(quantidade)
        if not livro or quantidade < 1 or livro.estoque < quantidade:
            transaction.set_rollback(True)
            messages.error(request, 'Um dos livros ficou sem estoque. Revise sua sacola.')
            return redirect('carrinho')
        ItemPedido.objects.create(
            pedido=pedido,
            livro=livro,
            quantidade=quantidade,
            preco_unitario=livro.preco,
        )
        livro.estoque -= quantidade
        livro.save(update_fields=['estoque'])
        total += livro.preco * quantidade
    pedido.total = total
    pedido.save(update_fields=['total'])
    sincronizar_pedido(pedido)
    request.session['carrinho'] = {}
    sincronizar_carrinho(request.user, {
        'local': {},
        'api': request.session.setdefault('carrinho_api', {}),
    })
    messages.success(request, f'Pedido #{pedido.pk} recebido com sucesso.')
    return redirect('pedidos')


@login_required
def pedidos(request):
    return render(request, 'pedidos.html', {'pedidos': Pedido.objects.filter(usuario=request.user).prefetch_related('itens__livro')})

@admin_required
def contatos(request):
    contatos = Contato.objects.all().order_by('-id')
    return render(request, "contatos.html", {'contatos': contatos})

def novoContato(request):
    if request.method == "POST":
        form = FormContato(request.POST)
        if form.is_valid():
            contato = form.save()
            sincronizar_contato(contato)
            messages.success(request, f"Obrigado pelo contato, {contato.nome}! Sua mensagem foi enviada com sucesso e retornaremos em breve.")
            return redirect('index')
        else:
            messages.error(request, "Não foi possível enviar sua mensagem. Por favor, confira os campos abaixo.")
    else:
        form = FormContato()
    
    return render(request, "novo-contato.html", {'form': form})

@staff_required
def excluirContato(request, id):
    contato = get_object_or_404(Contato, id=id)
    if request.method == 'POST':
        nome = contato.nome
        contato_id = contato.id
        contato.delete()
        remover_contato(contato_id)
        messages.success(request, f"Mensagem de contato enviada por {nome} foi excluída.")
    return redirect('contatos')

def integrantes(request):
    integrantes = []
    integrantes_erro = None
    vendedores = list(
        User.objects.filter(perfil__tipo_usuario="vendedor").order_by("username")
    )
    vendedor_por_nome = {
        (vendedor.get_full_name() or vendedor.username): vendedor
        for vendedor in vendedores
    }

    if supabase is None:
        integrantes_erro = "A equipe ficará disponível quando o Supabase for configurado."
    else:
        try:
            resposta = supabase.table("integrantes").select("*").execute()
            integrantes = resposta.data or []
        except Exception:
            logger.exception("Falha ao consultar integrantes no Supabase.")
            integrantes_erro = "Não foi possível carregar a equipe agora. Tente novamente mais tarde."

    nomes_presentes = set()
    for integrante in integrantes:
        nome = integrante.get("nome")
        nomes_presentes.add(nome)
        vendedor = vendedor_por_nome.get(nome)
        if vendedor is not None:
            integrante["usuario_id"] = vendedor.id
            integrante["vendedor"] = True
            if getattr(vendedor.perfil, "foto_url", ""):
                integrante["foto_url"] = vendedor.perfil.foto_url

    for vendedor in vendedores:
        nome = vendedor.get_full_name() or vendedor.username
        if nome not in nomes_presentes:
            integrantes.append({
                "nome": nome,
                "cargo": "Vendedor",
                "biografia": "Vendedor parceiro da Pétala Livraria.",
                "foto_url": getattr(vendedor.perfil, "foto_url", ""),
                "usuario_id": vendedor.id,
                "vendedor": True,
            })
    return render(request, "integrantes.html", {
        "integrantes": integrantes,
        "integrantes_erro": integrantes_erro,
    })

@admin_required
def addIntegrante(request):
    if supabase is None:
        messages.error(request, "Configure o Supabase para gerenciar integrantes.")
        return redirect("integrantes")
    if request.method == "POST":
        nome = (request.POST.get("nome") or "").strip()
        cargo = (request.POST.get("cargo") or "").strip()
        biografia = (request.POST.get("biografia") or "").strip()
        foto_url = (request.POST.get("foto_url") or "").strip()
        
        if not nome or not cargo or not biografia:
            messages.error(request, "Por favor, preencha todos os campos obrigatórios (nome, cargo e biografia).")
            return render(request, "add-integrante.html")

        try:
            supabase.table("integrantes").insert({
                "nome": nome,
                "cargo": cargo,
                "biografia": biografia,
                "foto_url": foto_url
            }).execute()
            messages.success(request, f'Integrante "{nome}" cadastrado com sucesso na equipe!')
            return redirect('integrantes')
        except Exception:
            logger.exception("Erro ao inserir integrante no Supabase.")
            messages.error(request, "Ocorreu um erro ao salvar o integrante no Supabase. Tente novamente.")
    
    return render(request, "add-integrante.html")

@admin_required
def editarIntegrante(request, id):
    if supabase is None:
        messages.error(request, "Configure o Supabase para gerenciar integrantes.")
        return redirect("integrantes")
    try:
        resposta = supabase.table("integrantes").select("*").eq("id", id).execute()
        if not resposta.data:
            messages.error(request, "Integrante não encontrado.")
            return redirect("integrantes")
    except Exception:
        logger.exception("Erro ao buscar integrante no Supabase.")
        messages.error(request, "Falha na comunicação com o Supabase ao carregar o integrante.")
        return redirect("integrantes")

    integrante = resposta.data[0]
    if request.method == "POST":
        nome = (request.POST.get("nome") or "").strip()
        cargo = (request.POST.get("cargo") or "").strip()
        biografia = (request.POST.get("biografia") or "").strip()
        foto_url = (request.POST.get("foto_url") or "").strip()

        if not nome or not cargo or not biografia:
            messages.error(request, "Por favor, preencha todos os campos obrigatórios (nome, cargo e biografia).")
            return render(request, "editar-integrante.html", {"integrante": integrante})

        try:
            supabase.table("integrantes").update({
                "nome": nome,
                "cargo": cargo,
                "biografia": biografia,
                "foto_url": foto_url,
            }).eq("id", id).execute()
            messages.success(request, f'Os dados do integrante "{nome}" foram atualizados com sucesso!')
            return redirect("integrantes")
        except Exception:
            logger.exception("Erro ao atualizar integrante no Supabase.")
            messages.error(request, "Não foi possível atualizar o integrante no Supabase. Tente novamente.")

    return render(request, "editar-integrante.html", {"integrante": integrante})

@admin_required
def delIntegrante(request, id):
    if supabase is None:
        messages.error(request, "Configure o Supabase para gerenciar integrantes.")
        return redirect("integrantes")
    try:
        resposta = supabase.table("integrantes").select("*").eq("id", id).execute()
        integrante = resposta.data[0] if resposta.data else None
        if integrante:
            vendedor = User.objects.filter(
                perfil__tipo_usuario="vendedor",
                first_name=integrante.get("nome"),
            ).first()
            if vendedor is None:
                vendedor = User.objects.filter(
                    perfil__tipo_usuario="vendedor",
                    username=integrante.get("nome"),
                ).first()
            if vendedor is None:
                for candidato in User.objects.filter(perfil__tipo_usuario="vendedor"):
                    if (candidato.get_full_name() or candidato.username) == integrante.get("nome"):
                        vendedor = candidato
                        break
            if vendedor is not None:
                remover_perfil(vendedor.id)
                vendedor.delete()
        supabase.table("integrantes").delete().eq("id", id).execute()
        messages.success(request, "Integrante removido da equipe com sucesso.")
    except Exception:
        logger.exception("Erro ao excluir integrante no Supabase.")
        messages.error(request, "Não foi possível remover o integrante no Supabase.")
    return redirect('integrantes')


@admin_required
def excluirVendedor(request, id):
    vendedor = get_object_or_404(
        User,
        id=id,
        perfil__tipo_usuario="vendedor",
    )
    nome = vendedor.get_full_name() or vendedor.username
    if request.method == "POST":
        if supabase is not None:
            try:
                supabase.table("integrantes").delete().eq("nome", nome).execute()
            except Exception:
                logger.exception("Não foi possível remover o vendedor da equipe no Supabase.")
        remover_perfil(vendedor.id)
        vendedor.delete()
        messages.success(request, "Vendedor excluído com sucesso.")
    return redirect("integrantes")

@api_view(['GET', 'POST'])
def categorias_api(request):
    if request.method=='GET':
        categorias = Categoria.objects.all()
        serializer = CategoriaSerializer(categorias, many=True)
        return Response(serializer.data)
    elif request.method=='POST':
        serializer = CategoriaSerializer(data=request.data)
        if serializer.is_valid():
            categoria = serializer.save()
            sincronizar_categoria(categoria)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'DELETE', 'PUT'])
def categoria_api(request, id):
    categoria = Categoria.objects.get(id=id)
    if request.method == 'GET':
        serializer = CategoriaSerializer(categoria)
        return Response(serializer.data)
    elif request.method=='DELETE':
        categoria_id = categoria.id
        categoria.delete()
        remover_categoria(categoria_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
    elif request.method == 'PUT':
        serializer = CategoriaSerializer(categoria, data=request.data)
        if serializer.is_valid():
            categoria = serializer.save()
            sincronizar_categoria(categoria)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@admin_required
def relatorios(request):
    servicos = Servico.objects.all()
    servicos_ativos = servicos.filter(ativo=True).count()
    servicos_inativos = servicos.filter(ativo=False).count()

    categorias = servicos.values('categoria__nome').annotate(quantidade=Count('id'))

    return render(request, 'relatorios.html', {
        'servicos_ativos': servicos_ativos,
        'servicos_inativos': servicos_inativos,
        'status_valores': [servicos_ativos, servicos_inativos],
        'categorias_labels': [
            item['categoria__nome'] or 'Sem categoria'
            for item in categorias
        ],
        'categorias_valores': [
            item['quantidade']
            for item in categorias
        ],
        'total_pedidos': Pedido.objects.count(),
        'faturamento': Pedido.objects.exclude(status='cancelado').values_list('total', flat=True),
    })