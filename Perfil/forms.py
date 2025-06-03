from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import MedicionCuerpo # Importa MedicionCuerpo

User = get_user_model()

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Username", "class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password", "class": "form-control"}))

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"placeholder": "Name", "class": "form-control"}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"placeholder": "Last Name", "class": "form-control"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "Email", "class": "form-control"}))
    username = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Username", "class": "form-control"}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password", "class": "form-control"}), label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Confirm Password", "class": "form-control"}), label="Confirm Password")
    agree_terms = forms.BooleanField(label='I agree with the Privacy Policy')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'agree_terms')

    def clean_password2(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password is not None and password != password2:
            raise forms.ValidationError("Your passwords must match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('foto_perfil',)

# ESTA ES LA CLASE CLAVE QUE DEBES VERIFICAR
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        # ASEGÚRATE DE QUE 'peso' Y 'estatura' NO ESTÉN EN ESTA LISTA
        fields = ['first_name', 'last_name', 'direccion', 'ciudad', 'pais', 'telefono', 'fecha_nacimiento', 'sexo', 'foto_perfil']

# Este formulario es para MedicionCuerpo, y está bien que tenga peso y estatura
class MedicionCuerpoForm(forms.ModelForm):
    class Meta:
        model = MedicionCuerpo
        fields = ['peso', 'estatura', 'ancho_hombros', 'ancho_caderas', 'icc_estimado', 'relacion_hombro_cintura', 'tipo_cuerpo']