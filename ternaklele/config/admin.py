from django.contrib.admin import AdminSite


class TernakLeleAdminSite(AdminSite):
    site_header = "🐟 Ternak Lele — Panel Admin"
    site_title = "Ternak Lele Admin"
    index_title = "Dashboard Pakar Perikanan"
