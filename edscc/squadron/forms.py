from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout
from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import Squadron


class SquadronForm(forms.ModelForm):

    home_base = forms.CharField(
        max_length=50,
        label=_("Home Base"),
        help_text=_(
            "Location of Squadron's home base, include the System and base name. (e.g. Sol - Abraham Lincoln)"
        ),
    )

    primary_language = forms.ChoiceField(
        label=_("Primary Language"),
        choices=Squadron.LANGUAGE_CHOICES,
        required=True,
        help_text=_(
            "Primary language of this Squadron used for announcements, messaging, etc."
        ),
    )

    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text=_("Write short description about your Squadron"),
        required=False,
    )

    welcome_message = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text=_(
            "The welcome message will be shown to commanders after logging in the system for the first time. (Use Markdown for formatting)"
        ),
        required=False,
    )

    require_approval = forms.BooleanField(
        label=_(
            "Require approval from squad leaders to associate their accounts to this Squadron on ED:SCC"
        )
    )

    uuid = forms.UUIDField(
        widget=forms.HiddenInput(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "squadron_form"
        self.helper.form_class = "form-text"
        self.helper.form_method = "post"
        # self.helper.layout = Layout(
        #     Field("uuid", type="hidden"),
        # )

    class Meta:
        model = Squadron
        fields = (
            "home_base",
            "primary_language",
            "description",
            "welcome_message",
            "require_approval",
            "uuid",
        )
