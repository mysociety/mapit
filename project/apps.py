from django.contrib.admin.apps import AdminConfig as BaseAdminConfig


class AdminConfig(BaseAdminConfig):
    default_site = "project.admin.AdminSite"
