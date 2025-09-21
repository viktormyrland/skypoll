# polls/forms.py
from django import forms
from .models import Poll, Ballot, Availability, VoteChoice
from .utils import next_weekend


class PollForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = ["title", "dz_leader", "description", "date_from", "date_to"]
        widgets = {
            "date_from": forms.DateInput(attrs={"type": "date"}),
            "date_to": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        saturday, sunday = next_weekend()
        week_number = saturday.isocalendar().week
        default_title = f'Helgehopping uke {week_number}'

        self.fields["date_from"].initial = saturday
        self.fields["date_to"].initial = sunday
        self.fields["title"].initial = default_title

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("date_from")
        end = cleaned_data.get("date_to")

        if start and end and end < start:
            self.add_error("date_to", "Sluttdato må være etter startdato.")
        return cleaned_data
