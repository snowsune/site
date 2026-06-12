from django.contrib import admin

from .models import TankLiquid, TankLog, TankSite


@admin.register(TankSite)
class TankSiteAdmin(admin.ModelAdmin):
    list_display = [
        "slug",
        "owner",
        "character_name",
        "tank_top_offset",
        "tank_bottom_offset",
    ]
    search_fields = ["slug", "owner__username"]
    raw_id_fields = ["owner"]


@admin.register(TankLiquid)
class TankLiquidAdmin(admin.ModelAdmin):
    list_display = ["name", "tank_site", "volume", "sort_order"]
    list_filter = ["tank_site"]


@admin.register(TankLog)
class TankLogAdmin(admin.ModelAdmin):
    list_display = ["tank_site", "date", "text"]
    list_filter = ["tank_site"]
