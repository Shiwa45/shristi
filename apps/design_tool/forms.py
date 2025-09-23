# apps/design_tool/forms.py
from django import forms
from apps.templates_mgmt.models import UserDesign

class SaveDesignForm(forms.ModelForm):
    class Meta:
        model = UserDesign
        fields = ('name', 'is_public')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'rounded'})
        }


