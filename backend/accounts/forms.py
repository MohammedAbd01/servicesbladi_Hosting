from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import Utilisateur

class UserEditForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    profile_picture = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Utilisateur
        fields = ('name', 'first_name', 'email', 'profile_picture')

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Ancien mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'autofocus': True, 'class': 'form-control'}),
    )
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
    )
    new_password2 = forms.CharField(
        label="Confirmation du nouveau mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
    )
