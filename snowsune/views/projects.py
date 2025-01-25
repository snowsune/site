from django.views import View
from django.shortcuts import render


class ProjectsView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "log/projects.html")
