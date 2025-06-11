from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class StyledUserCreationForm(UserCreationForm): # Custom subclass of UserCreationForm that allows for CSS customization
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super(StyledUserCreationForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'input-field', 
                'placeholder': field.label,
            })

class StyledAuthenticationForm(AuthenticationForm): # Custom subclass of AuthenticationForm that allows for CSS customization
    
    def __init__(self, *args, **kwargs):
        super(StyledAuthenticationForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'input-field', 
                'placeholder': field.label,
            })
