from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from chat.models import User
# Signup Form
class SignUpForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'user_name', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

class LoginForm(forms.Form):
    user_id = forms.CharField(max_length=25)
    password = forms.CharField(widget=forms.PasswordInput)

