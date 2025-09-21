# polls/signals.py
from django.db.models.signals import post_save
from django.db import transaction
from django.dispatch import receiver
from .models import Poll


@receiver(post_save, sender=Poll)
def create_poll_days_on_create(sender, instance: Poll, created, **kwargs):
    if not created:
        return
    # ensure we act after commit (important if called inside a transaction)
    transaction.on_commit(lambda: instance.generate_days())
