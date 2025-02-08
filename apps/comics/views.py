from django.shortcuts import render


def comics_landing(request):
    return render(request, "comics_home.html")
