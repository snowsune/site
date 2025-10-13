from django.shortcuts import render


def fops_redirect_view(request):
    """
    Super simple redirect for fops. Wont show a preview.
    Google analytics *should* track the redirect.
    """
    return render(request, "bot_manager/fops_redirect.html")
