from django.shortcuts import render


def fops_redirect_view(request):
    """
    Super simple redirect for fops. Wont show a preview.
    Google analytics *should* track the redirect.
    """

    # For google analytics tracking
    # https://support.google.com/analytics/thread/267260949/how-to-track-domain-before-it-redirects?hl=en
    redirect_url = (
        "/fops/?utm_source=redirect&utm_medium=meta_refresh&utm_campaign=fops_redirect"
    )

    context = {"redirect_url": redirect_url}

    return render(request, "bot_manager/fops_redirect.html", context)
