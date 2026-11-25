from django.contrib import admin

from .models import Amenity, BlockedDate, EventType, Venue, VenuePhoto


class VenuePhotoInline(admin.TabularInline):
    model = VenuePhoto
    extra = 0
    fields = ["image", "caption", "order"]


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "owner", "capacity_max", "price_per_day", "rating_avg", "is_published"]
    list_filter = ["is_published", "city", "event_types"]
    search_fields = ["name", "city", "area", "owner__email"]
    prepopulated_fields = {"slug": ["name"]}
    filter_horizontal = ["event_types", "amenities"]
    inlines = [VenuePhotoInline]


admin.site.register(EventType, admin.ModelAdmin)
admin.site.register(Amenity, admin.ModelAdmin)


@admin.register(BlockedDate)
class BlockedDateAdmin(admin.ModelAdmin):
    list_display = ["venue", "date", "reason"]
    list_filter = ["venue"]
