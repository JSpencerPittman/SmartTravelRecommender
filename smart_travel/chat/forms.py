from django import forms


class NewChatForm(forms.Form):
    title = forms.CharField(max_length=50, label="Title")
