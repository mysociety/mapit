from django.contrib import admin
from django.urls import path

from mapit.add_areas_from_file import admin_flow


class AdminSite(admin.AdminSite):
    # Override the default template to display the 'add areas from a file' view.
    index_template = "admin.html"

    def get_urls(self):
        """Add a view for adding areas from a file, not affiliated with a specific model."""
        urls = super().get_urls()
        my_urls = [
            path('add-areas-from-file/', self.admin_view(admin_flow.view))
        ]
        return my_urls + urls
