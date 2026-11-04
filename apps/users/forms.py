from django import forms


class EmailBlastForm(forms.Form):
    subject = forms.CharField(max_length=200)
    body = forms.CharField(
        label="Message",
        widget=forms.Textarea(attrs={"rows": 14, "class": "vLargeTextField"}),
    )
    confirm = forms.BooleanField(required=True)

    def __init__(self, *args, recipient_count=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].widget.attrs["class"] = "vTextField"
        self.fields["confirm"].label = f"Send this to {recipient_count} people"
