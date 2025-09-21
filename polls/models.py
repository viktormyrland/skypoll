from django.db import models
from django.urls import reverse
from datetime import timedelta, date
from .utils import generate_slug


class Poll(models.Model):
    slug = models.SlugField(unique=True, db_index=True)
    title = models.CharField("Tittel", max_length=200)
    dz_leader = models.CharField("Hoppleder", max_length=200)
    description = models.CharField("Informasjon", max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    date_from = models.DateField("Startdato")
    date_to = models.DateField("Sluttdato")

    class Meta:
        indexes = [models.Index(fields=["slug"])]

    def is_open(self):
        return date.today() <= self.date_to

    def generate_days(self, *, save=True):
        """Create PollDay rows for each day in [date_from, date_to]."""
        days = []
        d = self.date_from
        while d <= self.date_to:
            days.append(PollDay(poll=self, day=d))
            d += timedelta(days=1)
        if save:
            PollDay.objects.bulk_create(days, ignore_conflicts=True)
        return days

    def save(self, *args, **kwargs):
        if not self.slug:
            # keep generating until unique
            slug = generate_slug()
            while Poll.objects.filter(slug=slug).exists():
                slug = generate_slug()
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("poll_detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.title


class PollDay(models.Model):
    poll = models.ForeignKey(Poll, related_name="days",
                             on_delete=models.CASCADE)
    day = models.DateField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("poll", "day")]
        indexes = [models.Index(fields=["poll", "day"])]
        ordering = ["day"]

    def __str__(self):
        return f'{str(self.day)} ({self.poll.title})'


class VoteChoice(models.IntegerChoices):
    NO = 0, 'Nei'
    MAYBE = 1, 'Kanskje'
    YES = 2, 'Ja'


class Ballot(models.Model):
    poll = models.ForeignKey(
        Poll, related_name="ballots", on_delete=models.CASCADE)
    nickname = models.CharField(max_length=80)
    submitted_at = models.DateTimeField(auto_now_add=True)
    user_cookie = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.nickname} ("{self.poll.title}")'


class Availability(models.Model):
    ballot = models.ForeignKey(
        Ballot, related_name="availabilities", on_delete=models.CASCADE)
    day = models.ForeignKey(
        PollDay, related_name="availabilities",
        on_delete=models.CASCADE)
    status = models.PositiveSmallIntegerField(
        choices=VoteChoice.choices, blank=True, null=True)

    class Meta:
        unique_together = [("ballot", "day")]
        indexes = [models.Index(fields=["day", "status"])]

    def __str__(self): return f'{self.ballot.nickname}, {str(self.day)}'
