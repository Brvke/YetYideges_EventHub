from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["venue", "event_date", "guest", "guest_count", "status", "quoted_price", "created_at"]
    list_filter = ["status", "venue"]
    search_fields = ["venue__name", "guest__email"]
    date_hierarchy = "event_date"
