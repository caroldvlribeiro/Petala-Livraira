from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.contrib.auth.models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Nome de usuário",
        help_text="Informe o nome de usuário cadastrado na sua conta.",
        widget=forms.TextInput(attrs={
            "placeholder": "Ex: maria_silva",
            "autofocus": True,
            "class": "campo-input",
        }),
    )
    password = forms.CharField(
        label="Senha",
        help_text="Informe sua senha cadastrada.",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Digite sua senha",
            "class": "campo-input",
        }),
    )


class CadastroForm(UserCreationForm):
    username = forms.CharField(
        label="Nome de usuário",
        help_text="Obrigatório. Até 150 caracteres. Pode conter letras, números e @/./+/-/_.",
        widget=forms.TextInput(attrs={
            "placeholder": "Ex: maria_silva",
            "class": "campo-input",
        }),
    )
    email = forms.EmailField(
        label="Endereço de e-mail",
        required=True,
        help_text="Utilizado para identificação, acompanhamento de pedidos e recuperação de acesso.",
        widget=forms.EmailInput(attrs={
            "placeholder": "maria@exemplo.com",
            "class": "campo-input",
        }),
    )
    foto_url = forms.URLField(
        required=False,
        label="Link da foto de perfil",
        help_text="Opcional. Insira a URL direta da imagem (JPG/PNG). Vendedores com foto aparecem com destaque na equipe.",
        widget=forms.URLInput(attrs={
            "placeholder": "https://exemplo.com/minha-foto.jpg",
            "class": "campo-input",
        }),
    )
    tipo_usuario = forms.ChoiceField(
        choices=(
            ("cliente", "Cliente (comprar e acompanhar pedidos)"),
            ("vendedor", "Vendedor (vender livros e integrar a equipe)"),
        ),
        label="Tipo de conta",
        help_text="Escolha 'Cliente' para ler e adquirir livros ou 'Vendedor' para publicar títulos no catálogo.",
        initial="cliente",
        required=False,
        widget=forms.Select(attrs={
            "class": "campo-select",
        }),
    )

    class Meta:
        model = User
        fields = ("username", "email", "tipo_usuario", "foto_url", "password1", "password2")
        labels = {
            "password1": "Criar senha",
            "password2": "Confirmar senha",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "password1" in self.fields:
            self.fields["password1"].widget.attrs.update({
                "placeholder": "Crie uma senha forte (mínimo 8 caracteres)",
                "class": "campo-input",
            })
            self.fields["password1"].help_text = (
                "A senha deve conter pelo menos 8 caracteres e não pode ser inteiramente numérica."
            )
        if "password2" in self.fields:
            self.fields["password2"].widget.attrs.update({
                "placeholder": "Repita exatamente a mesma senha",
                "class": "campo-input",
            })
            self.fields["password2"].help_text = "Digite a mesma senha cadastrada acima para confirmação."


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="E-mail cadastrado",
        help_text="Enviaremos um link seguro para recuperação de senha caso este e-mail esteja cadastrado.",
        widget=forms.EmailInput(attrs={
            "placeholder": "seuemail@exemplo.com",
            "class": "campo-input",
            "autofocus": True,
        }),
    )


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "old_password" in self.fields:
            self.fields["old_password"].label = "Senha atual"
            self.fields["old_password"].help_text = "Informe a senha atual que você usa para entrar na conta."
            self.fields["old_password"].widget.attrs.update({
                "placeholder": "Digite sua senha atual",
                "class": "campo-input",
            })
        if "new_password1" in self.fields:
            self.fields["new_password1"].label = "Nova senha"
            self.fields["new_password1"].help_text = "Escolha uma senha forte com no mínimo 8 caracteres."
            self.fields["new_password1"].widget.attrs.update({
                "placeholder": "Digite a nova senha",
                "class": "campo-input",
            })
        if "new_password2" in self.fields:
            self.fields["new_password2"].label = "Confirmar nova senha"
            self.fields["new_password2"].help_text = "Repita a nova senha para confirmação."
            self.fields["new_password2"].widget.attrs.update({
                "placeholder": "Repita a nova senha",
                "class": "campo-input",
            })


class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "new_password1" in self.fields:
            self.fields["new_password1"].label = "Nova senha"
            self.fields["new_password1"].help_text = "Escolha uma senha forte com no mínimo 8 caracteres."
            self.fields["new_password1"].widget.attrs.update({
                "placeholder": "Digite sua nova senha",
                "class": "campo-input",
            })
        if "new_password2" in self.fields:
            self.fields["new_password2"].label = "Confirmar nova senha"
            self.fields["new_password2"].help_text = "Repita a nova senha digitada acima."
            self.fields["new_password2"].widget.attrs.update({
                "placeholder": "Repita a nova senha",
                "class": "campo-input",
            })
