from django import forms
from .models import Contato, Servico, Categoria


class FormServico(forms.ModelForm):
    class Meta:
        model = Servico
        fields = ("nome", "autor", "isbn", "descricao", "preco", "estoque", "imagem", "ativo", "categoria")
        labels = {
            "nome": "Título do livro",
            "autor": "Autor ou autora",
            "isbn": "Código ISBN",
            "descricao": "Sinopse e detalhes",
            "preco": "Preço de venda (R$)",
            "estoque": "Quantidade em estoque",
            "imagem": "Imagem de capa",
            "ativo": "Disponível para venda",
            "categoria": "Gênero / Categoria literária",
        }
        help_texts = {
            "nome": "Informe o título completo da obra.",
            "autor": "Nome do autor, autora ou organizador.",
            "isbn": "Identificador padrão do livro (ex: 978-85-359-0277-8).",
            "descricao": "Apresente uma breve descrição ou sinopse da história.",
            "preco": "Valor unitário em reais. Exemplo: 49.90.",
            "estoque": "Número de exemplares físicos disponíveis para pronta-entrega.",
            "imagem": "Envie uma foto ou ilustração de capa em JPG ou PNG.",
            "ativo": "Mantenha marcado para exibir este livro no catálogo público.",
            "categoria": "Classificação do livro para facilitar as buscas dos leitores.",
        }
        widgets = {
            "nome": forms.TextInput(attrs={
                "placeholder": "Ex: Dom Casmurro",
                "class": "campo-input",
            }),
            "autor": forms.TextInput(attrs={
                "placeholder": "Ex: Machado de Assis",
                "class": "campo-input",
            }),
            "isbn": forms.TextInput(attrs={
                "placeholder": "Ex: 978-85-359-0277-8",
                "class": "campo-input",
            }),
            "descricao": forms.Textarea(attrs={
                "placeholder": "Escreva a sinopse do livro, temas abordados e destaques da edição...",
                "rows": 4,
                "class": "campo-textarea",
            }),
            "preco": forms.NumberInput(attrs={
                "placeholder": "Ex: 39.90",
                "step": "0.01",
                "min": "0",
                "class": "campo-input",
            }),
            "estoque": forms.NumberInput(attrs={
                "placeholder": "Ex: 10",
                "min": "0",
                "class": "campo-input",
            }),
            "categoria": forms.Select(attrs={
                "class": "campo-select",
            }),
        }


class FormContato(forms.ModelForm):
    class Meta:
        model = Contato
        fields = ("nome", "email", "telefone", "mensagem")
        labels = {
            "nome": "Seu nome completo",
            "email": "Seu endereço de e-mail",
            "telefone": "Telefone para contato",
            "mensagem": "Sua mensagem",
        }
        help_texts = {
            "nome": "Como devemos chamar você.",
            "email": "Utilizaremos este e-mail para retornar seu contato.",
            "telefone": "Opcional. Inclua DDD para contato telefônico ou WhatsApp.",
            "mensagem": "Conte com detalhes sua dúvida, sugestão, elogio ou solicitação.",
        }
        widgets = {
            "nome": forms.TextInput(attrs={
                "placeholder": "Ex: Mariana Oliveira",
                "class": "campo-input",
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "mariana@exemplo.com",
                "class": "campo-input",
            }),
            "telefone": forms.TextInput(attrs={
                "placeholder": "Ex: (11) 98765-4321",
                "class": "campo-input",
            }),
            "mensagem": forms.Textarea(attrs={
                "placeholder": "Escreva aqui sua mensagem para a equipe da Pétala...",
                "rows": 5,
                "class": "campo-textarea",
            }),
        }
