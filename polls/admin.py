
from django.contrib import admin
from .models import Poll, PollDay, Availability, Ballot

admin.site.register(Poll)
admin.site.register(PollDay)
admin.site.register(Availability)
admin.site.register(Ballot)
