from django.urls import path
from .views import CreateURLView, RedirectURLView

urlpatterns = [
    path('', CreateURLView.as_view(), name='create_url'),
    path('<str:short_code>', RedirectURLView.as_view(), name='redirect_url'),
]
