from django.urls import path

from traductor_app.views import home, translation_details, translation_history

urlpatterns = [
    path("", home, name="home"),
    path("history/", translation_history, name="history"),
    path("details/<int:translation_id>/", translation_details, name="details"),
]
