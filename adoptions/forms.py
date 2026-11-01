import re

from django import forms

from .models import AdoptionRequest


class AdoptionRequestForm(forms.ModelForm):
    class Meta:
        model = AdoptionRequest
        fields = ['full_name', 'email', 'phone', 'message']
        labels = {
            'full_name': 'Your name',
            'phone': 'Phone (optional)',
            'message': 'Why would you like to adopt?',
        }
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if phone and not re.fullmatch(r'[0-9+()\-\s]{7,20}', phone):
            raise forms.ValidationError('Enter a valid phone number.')
        return phone
