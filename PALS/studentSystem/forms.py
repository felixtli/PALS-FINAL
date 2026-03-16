from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Profile

class StyledUserCreationForm(UserCreationForm):
    user_type = forms.ChoiceField(
        choices=Profile.USER_TYPES,
        widget=forms.Select,
        label="Study Group",
    )

    class Meta:
        model = User
        fields = ['username', 'user_type', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'input-field',
            })

        self.fields["user_type"].initial = "B"

class StyledAuthenticationForm(AuthenticationForm): # Custom subclass of AuthenticationForm that allows for CSS customization
    
    def __init__(self, *args, **kwargs):
        super(StyledAuthenticationForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'input-field', 
                'placeholder': field.label,
            })
