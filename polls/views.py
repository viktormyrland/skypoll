from .forms import PollForm
from django.db.models import Prefetch
from django.shortcuts import render, redirect, get_object_or_404
from .models import Poll, Availability, Ballot, VoteChoice
from .utils import generate_slug
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed


def create_poll(request):
    if request.method == "POST":
        form = PollForm(request.POST)
        if form.is_valid():
            poll = form.save()
            return redirect("poll_detail", slug=poll.slug)

    else:
        form = PollForm()
    return render(request, "polls/poll_form.html", {"form": form})


def poll_detail(request, slug):

    poll = get_object_or_404(Poll.objects.prefetch_related("days"), slug=slug)
    days = list(poll.days.all().order_by("day"))
    ballots = (
        poll.ballots.prefetch_related(Prefetch(
            "availabilities",
            queryset=Availability.objects.select_related("day")))
    ).order_by("submitted_at")

    for b in ballots:
        b.av_by_day = {a.day_id: a.status for a in b.availabilities.all()}

    rows = []
    for b in ballots:
        rows.append({
            "ballot": b,
            "statuses": [b.av_by_day.get(d.id) for d in days],
        })

    user_cookie = request.COOKIES.get("skypoll_user_id") or generate_slug()

    edit_ballot = Ballot.objects.filter(
        poll=poll, user_cookie=user_cookie).first()
    edit_statuses = {}
    nickname = ""
    edit_pairs = None  # <- list of (day, status) for the edit rowk

    if edit_ballot:
        nickname = edit_ballot.nickname
        avs = Availability.objects.filter(
            ballot=edit_ballot).values_list("day_id", "status")
        edit_statuses = {day_id: status for day_id, status in avs}

        edit_pairs = [(d, edit_statuses.get(d.id, 0))
                      for d in days]  # default 0 (No)
        print(edit_statuses)

    context = {
        "poll": poll,
        "days": days,
        "rows": rows,
        "id": user_cookie,
        "edit_ballot": edit_ballot,
        "edit_statuses": edit_statuses,
        "edit_pairs": edit_pairs,
        "nickname": nickname,
    }

    response = render(request, "polls/poll_detail.html", context)

    if request.COOKIES.get("skypoll_user_id") is None:
        response.set_cookie(
            "skypoll_user_id",
            user_cookie,
            max_age=60*60*24*365,
            httponly=True,
            samesite="Lax"

        )
    return response


def home_redirect(request):
    latest = Poll.objects.order_by("-created_at").first()
    if latest:
        return redirect("poll_detail", slug=latest.slug)
    return redirect("create_poll")


def vote(request: HttpRequest, slug: str) -> HttpResponse:
    """
    Handles POST from the form with hidden day_<id> fields and nickname.
    Upserts a Ballot for this poll + user_cookie, then (re)writes Availability rows.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    poll = get_object_or_404(Poll.objects.prefetch_related("days"), slug=slug)
    days = list(poll.days.all().order_by("day"))

    user_cookie = request.COOKIES.get("skypoll_user_id") or generate_slug()
    nickname = (request.POST.get("nickname") or "").strip()[:80]

    print(request.POST)
    # Collect statuses from POST: day_<id> -> 0/1/2
    statuses = {}
    for d in days:
        raw = request.POST.get(f"day_{d.id}", "-1")
        try:
            v = int(raw)
            if v == -1:
                continue
            if v not in (VoteChoice.NO, VoteChoice.MAYBE, VoteChoice.YES):
                # v = VoteChoice.NO
                continue
        except ValueError:
            # v = VoteChoice.NO
            continue
        statuses[d.id] = v

    with transaction.atomic():
        ballot, created = Ballot.objects.select_for_update().get_or_create(
            poll=poll,
            user_cookie=user_cookie,
            defaults={"nickname": nickname},
        )
        if not created and nickname:
            ballot.nickname = nickname
            ballot.save(update_fields=["nickname"])

        # Rewrite availabilities (simple & reliable)
        Availability.objects.filter(ballot=ballot).delete()
        Availability.objects.bulk_create(
            [
                Availability(ballot=ballot, day_id=d, status=statuses[d])
                for d in statuses
            ]
        )

    resp = redirect("poll_detail", slug=poll.slug)
    # Ensure cookie persists for future edits
    resp.set_cookie("skypoll_user_id", user_cookie,
                    max_age=60 * 60 * 24 * 365, samesite="Lax")
    return resp
