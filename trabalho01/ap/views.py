from decimal import Decimal
import hashlib
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models.aggregates import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
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

def index(request):
    livros = Servico.objects.filter(ativo=True).order_by('-criado_em')[:4]
    return render(request, "index.html", {'livros_destaque': livros})

def servicos(request):
    
    ## servicos = Servico.objects.all()
    servicos = Servico.objects.filter(ativo=True).exclude(preco=0)
     
    total_servicos = servicos.count()
    tem_servicos = servicos.exists()
    
    mais_barato = servicos.order_by('preco').first()
    mais_caro = servicos.order_by('-preco').first()
    
    
    #recupera o valor do formulário de busca enviado pelo usuário
    busca = request.GET.get('busca')
    if busca:
        servicos = servicos.filter(nome__icontains=busca)
        
    #recupera as categorias ativas para exibir no filtro
    categorias = Categoria.objects.filter(ativo=True)
    
    #recupera o valor do filtro de categoria enviado pelo usuário
    categoria = request.GET.get('categoria')
    if categoria:
        #aplica o filtro de categoria aos serviços
        servicos = servicos.filter(categoria_id=categoria)
        
    preco = request.GET.get('preco')
    if preco == 'baixo':
        servicos = servicos.filter(preco__lte=50)
    elif preco == 'medio':
        servicos = servicos.filter(preco__gt=50, preco__lte=250)
    elif preco == 'alto':
        servicos = servicos.filter(preco__gt=250)
    
    ordem = request.GET.get('ordem')
    if ordem == 'menor':
        servicos = servicos.order_by('preco')
    elif ordem == 'maior':
        servicos = servicos.order_by('-preco')
    elif ordem == 'nome':
        servicos = servicos.order_by('nome')

    contexto = {
        'servicos': servicos,
        'total_servicos': total_servicos,
        'tem_servicos': tem_servicos,
        'mais_barato': mais_barato,
        'mais_caro': mais_caro,
        'busca': busca,
        'categoria': categoria,
        'categorias': categorias,
        'preco': preco,
        'ordem' : ordem,
    }
        
    contexto['livros'] = servicos
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
            return redirect('servicos')

    return render (request, "add-servico.html", {'form': form})

@staff_required
def excluirServico(request, id):
    if is_administrator(request.user):
        servico = get_object_or_404(Servico, id=id)
    else:
        servico = get_object_or_404(Servico, id=id, vendedor=request.user)
    if request.method == 'POST':
        servico.imagem.delete(save=False)
        servico_id = servico.id
        servico.delete()
        remover_livro(servico_id)
    return redirect('servicos')

@staff_required
def editarServico(request, id):
    if is_administrator(request.user):
        servico = get_object_or_404(Servico, id=id)
    else:
        servico = get_object_or_404(Servico, id=id, vendedor=request.user)
    form = FormServico(request.POST or None, request.FILES or None, instance=servico)
    if request.POST:
        if form.is_valid():
            form.save()
            sincronizar_livro(servico)
            return redirect('servicos')

    return render(request, "editar-servico.html", {'form': form, 'livro': servico})

def produtos(request):
    livros = Servico.objects.filter(ativo=True)
    produtos_api = []
    api_erro = None
    try:
        resposta = requests.get(
            'https://openlibrary.org/search.json',
            params={'q': 'literatura brasileira', 'limit': 24},
            timeout=5,
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
    except (requests.RequestException, ValueError):
        api_erro = 'A vitrine de recomendações está indisponível no momento.'
    return render(request, "produtos.html", {
        'livros': livros,
        'produtos_api': produtos_api,
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
        carrinho.pop(str(id), None)
        request.session.modified = True
        if request.user.is_authenticated:
            sincronizar_carrinho(request.user, {
                'local': carrinho,
                'api': request.session.setdefault('carrinho_api', {}),
            })
    return redirect('carrinho')


@login_required
def remover_api_carrinho(request, key):
    if request.method == 'POST':
        carrinho_api = request.session.setdefault('carrinho_api', {})
        carrinho_api.pop(key, None)
        request.session.modified = True
        sincronizar_carrinho(request.user, {
            'local': _carrinho(request),
            'api': carrinho_api,
        })
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

def contatos(request):
    contatos = Contato.objects.all()
    return render(request, "contatos.html", {'contatos': contatos})

def novoContato(request):
    if request.method == "POST":
        form = FormContato(request.POST)
        if form.is_valid():
            contato = form.save()
            sincronizar_contato(contato)
            return redirect('index')
    else:
        form = FormContato()
    
    return render(request, "novo-contato.html", {'form': form})

@staff_required
def excluirContato(request, id):
    contato = get_object_or_404(Contato, id=id)
    if request.method == 'POST':
        contato_id = contato.id
        contato.delete()
        remover_contato(contato_id)
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
        nome = request.POST.get("nome")
        cargo = request.POST.get("cargo")
        biografia = request.POST.get("biografia")
        foto_url = request.POST.get("foto_url")
        
        supabase.table("integrantes").insert({
            "nome": nome,
            "cargo": cargo,
            "biografia": biografia,
            "foto_url": foto_url
        }).execute()
        
        return redirect('integrantes')
    
    return render(request, "add-integrante.html")

@admin_required
def editarIntegrante(request, id):
    if supabase is None:
        messages.error(request, "Configure o Supabase para gerenciar integrantes.")
        return redirect("integrantes")
    resposta = supabase.table("integrantes").select("*").eq("id", id).execute()
    if not resposta.data:
        raise Http404("Integrante não encontrado.")

    integrante = resposta.data[0]
    if request.method == "POST":
        supabase.table("integrantes").update({
            "nome": request.POST.get("nome"),
            "cargo": request.POST.get("cargo"),
            "biografia": request.POST.get("biografia"),
            "foto_url": request.POST.get("foto_url"),
        }).eq("id", id).execute()
        return redirect("integrantes")

    return render(request, "editar-integrante.html", {"integrante": integrante})

@admin_required
def delIntegrante(request, id):
    if supabase is None:
        messages.error(request, "Configure o Supabase para gerenciar integrantes.")
        return redirect("integrantes")
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
    
@staff_required
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