
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),  # Incluye las URLs de la app
    path('', RedirectView.as_view(url='/', permanent=True)),  # Redirección raíz
]