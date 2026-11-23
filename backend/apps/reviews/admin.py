from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["venue", "author", "rating", "created_at"]
    list_filter = ["rating", "venue"]
    search_fields = ["venue__name", "author__email", "comment"]
