from django.views import View
from django.shortcuts import render
from datetime import datetime


class ComicsView(View):
    def get(self, request, *args, **kwargs):
        context = {"year": datetime.now().year}
        return render(request, "log/home.html", context)
