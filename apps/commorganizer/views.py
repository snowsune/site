from django.shortcuts import render

# Create your views here.


def commorganizer_landing(request):
    return render(request, "commorganizer_home.html")
