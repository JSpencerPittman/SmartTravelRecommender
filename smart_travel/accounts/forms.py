from django import forms
from accounts.models import AccountModel
from django.contrib.auth.hashers import make_password, check_password


# Signup Form
class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = AccountModel
        fields = ["first_name", "last_name", "user_name"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit: bool = True):
        account = super().save(commit=False)
        account.password_hash = make_password(self.cleaned_data["password"])
        if commit:
            account.save()
        return account


class LoginForm(forms.Form):
    user_id = forms.CharField(max_length=25)
    password = forms.CharField(widget=forms.PasswordInput)
