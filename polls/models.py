from django.db import models
from django.utils import timezone
from datetime import timedelta


class Poll(models.Model):
    slug = models.SlugField(unique=True, db_index=True)
    title = models.CharField(max_length=200)
    dz_leader = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    date_from = models.DateField()
    date_to = models.DateField()

    class Meta:
        indexes = [models.Index(fields=["slug"])]

    def is_open(self):
        return timezone.now() < self.date_to

    def generate_days(self, *, save=True):
        """Create PollDay rows for each day in [start_date, end_date]."""
        days = []
        d = self.start_date
        while d <= self.end_date:
            days.append(PollDay(poll=self, day=d))
            d += timedelta(days=1)
        if save:
            PollDay.objects.bulk_create(days, ignore_conflicts=True)
        return days


class PollDay(models.Model):
    poll = models.ForeignKey(Poll, related_name="days",
                             on_delete=models.CASCADE)
    day = models.DateField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("poll", "day")]
        indexes = [models.Index(fields=["poll", "day"])]
        ordering = ["day"]
