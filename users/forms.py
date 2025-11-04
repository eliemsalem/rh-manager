# users/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _


class LoginForm(AuthenticationForm):
    """
    Custom login form with Bootstrap styling.
    """
    username = forms.CharField(
        label=_("Username"),
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your username",
            "autofocus": True
        })
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your password"
        })
    )

    remember_me = forms.BooleanField(
        label=_("Remember me"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    def confirm_login_allowed(self, user):
        """Optional: block inactive users"""
        if not user.is_active:
            raise forms.ValidationError(
                _("This account is inactive."),
                code="inactive",
            )
