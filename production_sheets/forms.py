from django import forms
from .models import ProductionSheet

class ProductionSheetForm(forms.ModelForm):
    class Meta:
        model = ProductionSheet
        fields = ['excel_file', 'origin']
        widgets = {
            'origin': forms.Select(attrs={'class': 'form-control'}),
            'excel_file': forms.FileInput(attrs={'class': 'form-control'})
        }