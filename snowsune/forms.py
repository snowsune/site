from django import forms
from .models import Entry


class EntryForm(forms.Form):
    battery = forms.CharField(max_length=3, label="Battery")
    ready = forms.BooleanField(label="Comp Ready", required=False)
    condition = forms.TypedChoiceField(
        choices=Entry.Condition,
        coerce=int,
        label="Condition",
        empty_value=Entry.Condition.NA,
    )
    charge = forms.DecimalField(
        label="Charge", max_digits=4, decimal_places=1, required=False
    )
    rint = forms.DecimalField(
        label="Resistance", max_digits=5, decimal_places=3, required=False
    )
    memo = forms.CharField(required=False)
