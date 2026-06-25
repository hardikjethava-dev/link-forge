from django.urls import path
from .views import StatsDashboardView

urlpatterns = [
    path('', StatsDashboardView.as_view(), name='stats_dashboard'),
]
