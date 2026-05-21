"""URL configuration for atlas project."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # Django's built-in auth views: /login/, /logout/, password reset, etc.
    path('', include('django.contrib.auth.urls')),
    # Our app's URLs: /, /signup/, /compare/
    path('', include('atlasdemo.urls')),
]
