# polls/utils.py
import datetime
import secrets
import base64


def next_weekend():
    today = datetime.date.today()
    # weekday(): Monday=0 … Sunday=6
    days_until_saturday = (5 - today.weekday()) % 7
    saturday = today + datetime.timedelta(days=days_until_saturday)
    sunday = saturday + datetime.timedelta(days=1)
    return saturday, sunday


def generate_slug(length=10):
    token = base64.urlsafe_b64encode(
        secrets.token_bytes(4)).decode("ascii").rstrip("=")
    return token[:length]
