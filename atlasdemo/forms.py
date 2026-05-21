from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignupForm(UserCreationForm):
    """Extends Django's built-in UserCreationForm to also require an email."""

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class CompareUploadForm(forms.Form):
    """Two file inputs for the comparison page. Accepts .xlsx, .xls, .csv."""

    file_a = forms.FileField(label='First file')
    file_b = forms.FileField(label='Second file')

    def _validate_file(self, f):
        name = f.name.lower()
        if not (name.endswith('.xlsx') or name.endswith('.xls') or name.endswith('.csv')):
            raise forms.ValidationError(
                f"Unsupported file type: {f.name}. Upload .xlsx, .xls, or .csv."
            )
        return f

    def clean_file_a(self):
        return self._validate_file(self.cleaned_data['file_a'])

    def clean_file_b(self):
        return self._validate_file(self.cleaned_data['file_b'])
