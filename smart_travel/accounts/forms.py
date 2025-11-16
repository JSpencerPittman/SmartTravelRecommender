from django import forms
from accounts.models import AccountModel


# Signup Form
class SignUpForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = AccountModel
        fields = ["first_name", "last_name", "user_name", "password_hash"]
        widgets = {
            "password_hash": forms.PasswordInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password_hash")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class LoginForm(forms.Form):
    user_id = forms.CharField(max_length=25)
    password = forms.CharField(widget=forms.PasswordInput)
