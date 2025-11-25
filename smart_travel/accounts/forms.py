from django import forms  # type: ignore
from accounts.models import AccountModel
from accounts.cqrs.commands import CommandCreateUser


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

    def save(self, _: bool = True) -> bool:
        return CommandCreateUser.execute(
            self.cleaned_data["first_name"],
            self.cleaned_data["last_name"],
            self.cleaned_data["user_name"],
            self.cleaned_data["password"],
        )


class LoginForm(forms.Form):
    user_id = forms.CharField(max_length=25)
    password = forms.CharField(widget=forms.PasswordInput)
