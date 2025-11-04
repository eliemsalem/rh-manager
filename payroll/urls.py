from django.urls import path, include
from . import views

app_name = 'payroll'



urlpatterns = [
    path('', views.payroll_list, name='payroll_list'),
    path('generate/', views.generate_month_for_actives, name='payroll_generate'),
    path('<int:pk>/edit/', views.payroll_edit, name='payroll_edit'),
    path('<int:pk>/pdf/', views.payroll_pdf, name='payroll_pdf'),
    path('bulk/<int:year>/<int:month>/zip/', views.bulk_zip_month, name='payroll_bulk_zip'),
    path("export/", views.payroll_export_excel, name="payroll_export_excel"),
    #path("", include("django.contrib.auth.urls")),
    path('', include('users.urls')),  # ✅ important ici
    path("stats/", views.payroll_stats, name="payroll_stats"),  # 👈 ADD THIS LINE


]

