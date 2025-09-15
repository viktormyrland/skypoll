from django.db import models


class Ballot(models.Model):
    poll = models.ForeignKey(
        "polls.Poll", related_name="ballots", on_delete=models.CASCADE)
    nickname = models.CharField(max_length=80)
    submitted_at = models.DateTimeField(auto_now_add=True)
    user_cookie = models.CharField(max_length=100)
