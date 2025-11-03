from django import forms


class NewChatForm(forms.Form):
    title = forms.CharField(max_length=50, label="Title")


class MessageForm(forms.Form):
    message = forms.CharField(max_length=200, label="Message")
