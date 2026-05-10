from datetime import datetime

from django.shortcuts import render
from django.views import View

from apps.tanks_manager.models import TankSite


class ToolsView(View):
    def get(self, request, *args, **kwargs):
        user_tank_slug = None
        if request.user.is_authenticated:
            user_tank_slug = (
                TankSite.objects.filter(owner_id=request.user.pk)
                .values_list("slug", flat=True)
                .first()
            )
        context = {
            "year": datetime.now().year,
            "user_tank_slug": user_tank_slug,
        }
        return render(request, "tools.html", context)
