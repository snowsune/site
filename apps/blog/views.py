from django.shortcuts import render


def blog_landing(request):
    return render(request, "landing.html")
