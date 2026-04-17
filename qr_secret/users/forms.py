from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    """Форма для регистрации пользователя."""
    email = forms.EmailField(required=True)
    display_name = forms.CharField(required=False, max_length=120)

    class Meta:
        model = User
        fields = ['username', 'email', 'display_name', 'password1', 'password2']

    def save(self, commit=True):
        """Сохраняет профиль пользователя."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            user.profile.display_name = self.cleaned_data.get('display_name', '')
            user.profile.save()
        return user