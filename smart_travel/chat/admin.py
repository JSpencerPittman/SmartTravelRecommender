from django.contrib import admin
from chat.models import ConversationModel
from django.shortcuts import render  # type: ignore
from django.urls import path  # type: ignore


def usage_statistics_page(request):
    return render(request, "usage.html", {})


original_get_urls = admin.site.get_urls


def get_admin_urls():
    custom_urls = [
        path(
            "usage-statistics",
            admin.site.admin_view(usage_statistics_page),
            name="usage_statistics",
        )
    ]
    return custom_urls + original_get_urls()


admin.site.get_urls = get_admin_urls

admin.site.register(ConversationModel)
