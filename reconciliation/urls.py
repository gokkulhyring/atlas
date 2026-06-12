from django.urls import path

from . import views

urlpatterns = [
    path("", views.ReconciliationView.as_view(), name="reconciliation_view"),
]
