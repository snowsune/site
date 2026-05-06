from django.contrib import admin

from .models import TankClone, TankLiquid, TankLog, TankSettings


@admin.register(TankSettings)
class TankSettingsAdmin(admin.ModelAdmin):
    list_display = ["id", "tank_top_offset", "tank_bottom_offset"]


admin.site.register(TankClone)
admin.site.register(TankLiquid)
admin.site.register(TankLog)
