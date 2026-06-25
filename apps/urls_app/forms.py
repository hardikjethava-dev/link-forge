from django import forms
from .models import ShortURL
import string

class ShortURLForm(forms.ModelForm):
    """
    Form for creating a shortened URL with optional custom short code.
    """
    custom_code = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': 'Custom alias (optional)',
            'class': 'form-input'
        }),
        help_text="Leave blank for a random code."
    )

    class Meta:
        model = ShortURL
        fields = ['original_url']
        widgets = {
            'original_url': forms.URLInput(attrs={
                'placeholder': 'https://example.com/very/long/path',
                'class': 'form-input',
                'required': 'required'
            })
        }

    def clean_custom_code(self):
        code = self.cleaned_data.get('custom_code')
        if not code:
            return None
            
        # Validate that the code uses Base62 characters
        allowed = string.digits + string.ascii_letters + '-_'
        for char in code:
            if char not in allowed:
                raise forms.ValidationError("Custom alias can only contain letters, digits, hyphens, and underscores.")
                
        # Check uniqueness
        if ShortURL.objects.filter(short_code=code).exists():
            raise forms.ValidationError("This custom alias is already in use.")
            
        return code
