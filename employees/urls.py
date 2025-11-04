from django.urls import path
from . import views

app_name = "employees"

urlpatterns = [
    path("", views.employee_list, name="employee_list"),
    path("inactive/", views.employee_inactive_list, name="employee_inactive_list"),
    path("<int:pk>/", views.employee_detail, name="employee_detail"),
    path("add/", views.employee_add, name="employee_add"),
    path("delete/<int:pk>/", views.employee_delete, name="employee_delete"),
    path("import/", views.employee_import_excel, name="employee_import_excel"),
    path("import/template/", views.download_template, name="download_template"),
]
