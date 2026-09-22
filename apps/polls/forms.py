from django import forms

from .models import Poll


class VoteForm(forms.Form):
    """Single or multi choice vote form, built from a poll's options."""

    def __init__(self, poll, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.poll = poll
        choices = [(c.pk, c.text) for c in poll.choices.all()]

        if poll.choice_type == Poll.CHOICE_SINGLE:
            self.fields["choice"] = forms.ChoiceField(
                choices=choices,
                widget=forms.RadioSelect,
                required=True,
                label="Your vote",
            )
        else:
            self.fields["choices"] = forms.MultipleChoiceField(
                choices=choices,
                widget=forms.CheckboxSelectMultiple,
                required=True,
                label="Your votes",
            )

    def clean(self):
        cleaned = super().clean()
        poll = self.poll
        valid_ids = {c.pk for c in poll.choices.all()}

        if poll.choice_type == Poll.CHOICE_SINGLE:
            raw = cleaned.get("choice")
            if not raw:
                raise forms.ValidationError("Pick one option.")
            choice_id = int(raw)
            if choice_id not in valid_ids:
                raise forms.ValidationError("That option is not on this poll.")
            cleaned["choice_ids"] = [choice_id]
        else:
            raw_list = cleaned.get("choices") or []
            if not raw_list:
                raise forms.ValidationError("Pick at least one option.")
            choice_ids = [int(pk) for pk in raw_list]
            if any(pk not in valid_ids for pk in choice_ids):
                raise forms.ValidationError("One of those options is not on this poll.")
            if poll.max_choices and len(choice_ids) > poll.max_choices:
                raise forms.ValidationError(
                    f"You can pick at most {poll.max_choices} option"
                    f"{'s' if poll.max_choices != 1 else ''}."
                )
            cleaned["choice_ids"] = choice_ids

        return cleaned
