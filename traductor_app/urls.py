from django.urls import path, include

from traductor_app.views import home, results, translation_history, translation_details
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', home, name='home'),
    path('results/', results, name='results'),
    path('history/', translation_history, name='history'),
    path('details/<int:translation_id>/', translation_details, name='details'),
]