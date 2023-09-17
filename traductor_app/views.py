# Create your views here.
from django.shortcuts import render, redirect

from .api_client import APIFunTranslation  # Importa la función de traducción
from .models import Translation


def home(request):
    if request.method == 'POST':
        # Obtener el texto ingresado por el usuario
        text_to_translate = request.POST.get('text_to_translate', '')
        # Obtener el idioma de destino seleccionado
        target_language = request.POST.get('target_language', '')
        # Realizar la traducción
        translator = APIFunTranslation()
        translated_text = translator.translate(target_language, text_to_translate)
        # Redirigir a la vista de resultados
        translation = Translation(
            user=request.user,
            original_text=text_to_translate,
            translated_text=translated_text,
            target_language=target_language
        )

        translation.save()

        return results(request, translated_text)

    return render(request, 'translation/home.html', {'languages': ['sith', 'yoda', 'klingon', 'enderman', 'dothraki', 'emoji', 'quenya', 'groot', 'draconic', ]})


def results(request, translated_text):
    return render(request, 'translation/results.html', {'translated_text': translated_text})


def translation_history(request):
    # Lógica para obtener el historial de traducciones del usuario
    translations = Translation.objects.filter(user=request.user).order_by('-translation_date')
    return render(request, 'translation/history.html', {'translations': translations})


def translation_details(request, translation_id):
    # Lógica para obtener los detalles de una traducción específica
    translation = Translation.objects.get(id=translation_id)
    return render(request, 'translation/details.html', {'translation': translation})
