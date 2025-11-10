# flake8 /home/laurent/projects/django-web-app/jenniferperseverante_dev_site/jp_viz/views_contact.py

from django.shortcuts import render
from django.core.mail import EmailMessage
from jpdev_viz.models import Message

from datetime import datetime

from .contact_class import Contact


# --------------------------------------------------
# Page avec Formulaire de contact générique
# --------------------------------------------------
def generic(request):
    # Detect language from Url
    url = request.build_absolute_uri()
    r = None

    language_settings = {
        'fr': {
            'language_code': "fr",
            'html': {
                'title': "Contact",
                'description': "Formulaire pour contacter Jennifer Perseverante, maquilleuse professionnelle",
            },
            'hero': {
                'title': "Contactez-moi !",
                'subtitle': "N'hésitez-pas à me contacter pour avoir plus d'information,<br>pour réserver une séance de maquillage, etc.",
                'image': {
                    'src': "contact.avif",
                    'alt': "Image de la page de contact",
                },
            },
        },
        'en': {
            'language_code': "en",
            'html': {
                'title': "Contact",
                'description': "Form to contact Jennifer Perseverante, professional makeup artist",
            },    
            'hero': {
                'title': "Contact Me!",
                'subtitle': "Do not hesitate to contact me for more information, to book a makeup session, etc.",
                'image': {
                    'src': "contact.avif",
                    'alt': "Image de la page de contact",
                },
            },
        },
        'es': {
            'language_code': "es",
            'html': {
                'title': "Contacto",
                'description': "Formulario para contactar con Jennifer Perseverante, maquilladora profesional",
            },    
            'hero': {
                'title': "¡Contáctame!",
                'subtitle': "No dudes en contactar conmigo para más información, reservar una sesión de maquillaje, etc.",
                'image': {
                    'src': "contact.avif",
                    'alt': "Image de la page de contact",
                },
            },
        },
    }

    # Determines the language based on the URL, otherwise uses 'fr' as default
    language_code = 'fr'  # Default value
    for code in language_settings.keys():
        if f'/{code}/' in url:
            language_code = code
            break

    lang_config = language_settings[language_code]

    # Send email and save in DB ?
    if request.method == 'POST':
        r = Contact(lang_config['language_code'], 'generic', url).process(request)

    return render(
        request,
        'jp_viz/article.html',
        {
            'language_code': lang_config['language_code'],
            'html': lang_config['html'],
            'hero': lang_config['hero'],
            'article': {
                'family': 'generic',
                'language_code': lang_config['language_code'],
                'translated_slugs': {
                    'fr': 'contact',
                    'en': 'contact-us',
                    'es': 'contacto',
                }
            },
            'contact_form': Contact(lang_config['language_code'], 'generic', url).get_texts(),
            'response': r,
        }
    )
