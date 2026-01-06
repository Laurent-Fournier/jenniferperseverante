# flake8 /home/laurent/projects/django-web-app/jenniferperseverante_dev_site/jp_viz/views_contact.py

from django.shortcuts import render
from django_ratelimit.decorators import ratelimit

import os
from urllib.parse import urlparse
from .contact_class import Contact
from .navbar_class import Navbar

# --------------------------------------------------
# Page avec Formulaire de contact générique
# --------------------------------------------------
@ratelimit(key='ip', rate='3/m', method='POST', block=True)
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
    lg = 'fr'  # Default value
    for code in language_settings.keys():
        if request.path.startswith(f'/{code}/'):
            lg = code
            break

    lang_config = language_settings[lg]

    contact = Contact(lang_config['language_code'], 'generic', url)

    if request.method == 'POST':
        # Send email and save in DB ?
        r = contact.process(request)

    all_languages = ['fr', 'en', 'es']
    other_languages = [lang for lang in all_languages if lang != lg]

    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    return render(
        request,
        'article.html',
        {
            "environment": os.getenv('ENVIRONMENT'),
            'base_url': base_url,
            "html": {
                "title": lang_config['html']['title'],
                "description": lang_config['html']['description'],
            },           
            'other_languages': other_languages,
            'navbar': Navbar(lg).to_json(),  
            'lg': lg,
            'hero': lang_config['hero'],
            'slugs_lg': {'fr': 'contact', 'en': 'contact-us', 'es': 'contacto'},
            'article': {
                'family': 'generic',
                'language_code': lg,
                'slugs_lg': {
                    'fr': 'contact',
                    'en': 'contact-us',
                    'es': 'contacto',
                }
            },
            'contact_form': contact.get_texts(),
            'response': r
        }
    )
