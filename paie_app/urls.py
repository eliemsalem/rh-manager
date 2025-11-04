from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # --- Django Admin ---
    path("admin/", admin.site.urls),

    # --- Application principale (Employés) ---
    path("", include("employees.urls")),

    # --- Application Paie ---
    path("payroll/", include("payroll.urls")),

    # --- Authentification (login / logout) ---
    # Les routes /login/ et /logout/ sont gérées par l'app "users"
    path("", include("users.urls")),
]

# --- Gestion des fichiers médias (PDF, images, etc.) ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


