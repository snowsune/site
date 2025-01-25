from django.views import View
from django.shortcuts import render
from datetime import datetime


class HomeView(View):
    def get(self, request, *args, **kwargs):
        context = {"year": datetime.now().year}
        return render(request, "home.html", context)
