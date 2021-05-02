from django import forms

from .models import JournalLog


class JournalLogForm(forms.ModelForm):
    class Meta:
        model = JournalLog
        fields = ("file",)
