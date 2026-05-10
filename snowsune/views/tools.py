from datetime import datetime

from django.shortcuts import render
from django.views import View

from apps.tanks_manager.models import tank_site_slug_for_user


class ToolsView(View):
    def get(self, request, *args, **kwargs):
        context = {
            "year": datetime.now().year,
            "user_tank_slug": tank_site_slug_for_user(request.user),
        }
        return render(request, "tools.html", context)
