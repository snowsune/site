from django.shortcuts import render
import random
from .models import ThankYou


def thank_you_view(request):
    """Display thank you entries with random ordering for entries with order=0"""

    # Get entries with manual ordering first
    ordered_entries = ThankYou.objects.filter(order__gt=0).order_by("order")

    # Get entries that should be randomized (order=0)
    random_entries = list(ThankYou.objects.filter(order=0))

    # Randomize the order of entries with order=0
    random.shuffle(random_entries)

    # Combine ordered and randomized entries
    all_entries = list(ordered_entries) + random_entries

    context = {
        "thank_you_entries": all_entries,
    }

    return render(request, "thank_yous/thank_you.html", context)
