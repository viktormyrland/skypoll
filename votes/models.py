from django.db import models


class VoteChoice(models.IntegerChoices):
    NO = 0, 'Nei'
    MAYBE = 1, 'Kanskje'
    YES = 2, 'Ja'


class Ballot(models.Model):
    poll = models.ForeignKey(
        "polls.Poll", related_name="ballots", on_delete=models.CASCADE)
    nickname = models.CharField(max_length=80)
    submitted_at = models.DateTimeField(auto_now_add=True)
    user_cookie = models.CharField(max_length=100)


class Availability(models.Model):
    ballot = models.ForeignKey(
        Ballot, related_name="availabilities", on_delete=models.CASCADE)
    day = models.ForeignKey(
        "polls.PollDay", related_name="availabilities",
        on_delete=models.CASCADE)
    status = models.PositiveSmallIntegerField(
        choices=VoteChoice.choices, default=VoteChoice.NO, blank=True)

    class Meta:
        unique_together = [("ballot", "day")]
        indexes = [models.Index(fields=["day", "status"])]
