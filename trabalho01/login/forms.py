from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CadastroForm(UserCreationForm):
    email = forms.EmailField(required=True)
    foto_url = forms.URLField(
        required=False,
        label='Link da foto',
        help_text='Opcional para vendedores.',
    )
    tipo_usuario = forms.ChoiceField(
        choices=(
            ("cliente", "Cliente"),
            ("vendedor", "Vendedor"),
        ),
        label="Tipo de conta",
        help_text="Vendedores podem cadastrar livros no catálogo.",
        required=False,
    )

    class Meta:
        model = User
        fields = ("username", "email", "tipo_usuario", "foto_url", "password1", "password2")
        labels = {
            'username': 'Nome de usuário',
            'email': 'Email',
            'password1': 'Senha',
            'password2': 'Confirmação de senha',
        }
