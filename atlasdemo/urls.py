from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('compare/', views.compare, name='compare'),
    path('compare/<uuid:job_id>/', views.comparison_status, name='comparison_status'),
]
