from django.urls import path

from traductor_app.views import (
    TranslationHistoryView,
    export_history,
    home,
    translation_delete,
    translation_details,
)

urlpatterns = [
    path("", home, name="home"),
    path("history/", TranslationHistoryView.as_view(), name="history"),
    path("history/export/", export_history, name="export_history"),
    path("details/<int:translation_id>/", translation_details, name="details"),
    path("delete/<int:translation_id>/", translation_delete, name="delete"),
]
