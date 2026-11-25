from django.db import models

# Create your models here.

class Categoria(models.Model):
    nome = models.CharField(max_length=100)  
    descricao = models.TextField(blank=True)  
    ativo = models.BooleanField(default=True)
    def __str__(self):
        return self.nome

class Servico(models.Model):
    nome = models.CharField(max_length=100, verbose_name='Título')
    descricao = models.TextField(blank=True, verbose_name='Sinopse')
    preco = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço')
    imagem = models.ImageField(upload_to='servicos/', blank=True, null=True, verbose_name='Capa')
    autor = models.CharField(max_length=120, blank=True, verbose_name='Autor')
    isbn = models.CharField(max_length=20, blank=True, verbose_name='ISBN')
    estoque = models.PositiveIntegerField(default=10, verbose_name='Estoque')
    ativo = models.BooleanField(default=True, verbose_name='Disponível')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='servicos', blank=True, null=True)
    vendedor = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='livros',
        blank=True,
        null=True,
    )
    def __str__(self):
        return self.nome

    @property
    def livro(self):
        """Nome semântico para o catálogo, mantendo compatibilidade com o legado."""
        return self.nome

    @property
    def imagem_url(self):
        if not self.imagem:
            return ""
        nome = str(self.imagem.name)
        if nome.startswith("http://") or nome.startswith("https://"):
            return nome
        import os
        from pathlib import Path
        supabase_url = os.getenv("SUPABASE_URL", "https://rcgdynwvqfscixmhvxsj.supabase.co")
        filename = Path(nome).name
        return f"{supabase_url}/storage/v1/object/public/livros/capas/{self.id}_{filename}"
    
class Contato(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    telefone = models.CharField(max_length=20, blank=True)
    mensagem = models.TextField() 
    
    def __str__(self):
        return self.nome


class Pedido(models.Model):
    STATUS = [
        ('recebido', 'Recebido'),
        ('processando', 'Em preparação'),
        ('enviado', 'Enviado'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='pedidos')
    status = models.CharField(max_length=20, choices=STATUS, default='recebido')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-criado_em',)

    def __str__(self):
        return f'Pedido #{self.pk}'


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    livro = models.ForeignKey(Servico, on_delete=models.PROTECT, related_name='itens_pedido')
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.quantidade * self.preco_unitario