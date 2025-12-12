from django.shortcuts import render
from django.http import HttpResponse

from django.db.models import Q

from .models import Article, ArticleLg

import os
import os.path
from PIL import Image
from dotenv import load_dotenv

from .navbar_class import Navbar
    
# ------------
# Gallery
# ------------
def gallery(request):

    load_dotenv()  # load variables from .env
    
    # Source: Shutterstock
    shutterstock_sources = [
        'accueil-cours-de-maquillage.jpg',
        'accueil-enterrement-de-vie-de-jeune-fille.jpg',
        'accueil-maquillage-a-domicile.jpg',
        'accueil-maquillage-pour-fetes.jpg',
        'accueil-maquillage-pour-mariage.jpg',
        'accueil-maquillage-pour-shooting-photo.jpg',
        'maquillage-de-soiree-personnalise.jpg',
        'maquillage-de-soiree-professionnel.jpg',
        'maquillage-de-soiree-professionnel-briller.jpg',
        'maquillage-de-soiree-studio-domicile.jpg',
        'maquillage-enterrement-de-vie-de-jeune-fille.jpg',
        'maquillage-entre-filles.jpg',
        'maquillage-entreprise.jpg',
    ]
    
    # Source: Email
    email_sources = [
        'Charlenne-Fabien-Mariage-0105.jpg',
        'Charlenne-Fabien-Mariage-0119.jpg',
        'Charlenne-Fabien-Mariage-0120.jpg',
        'Charlenne-Fabien-Mariage-0134.jpg',
        'IMG_0149.jpg',
        'IMG_0240.jpg',
        'IMG_0479.jpg',
        'IMG_0483.jpg',
        'IMG_0723.jpg',
        'IMG_0728.jpg',
        'IMG_0737.jpg',
        'IMG_0758.jpg',
        'IMG_0761.jpg',
        'IMG_1020.jpg',
        'IMG_1029.jpg',
        'IMG_1081.jpg',
        'IMG_1636.jpg',
        'IMG_2636.jpg',
        'IMG_5369.jpg',
        'IMG_6294.jpg',
        'IMG_6382.jpg',
        'IMG_6817.jpg',
        'IMG_6822.jpg',
        'IMG_6823.jpg',
        'IMG_6824.jpg',
        'IMG_6825.jpg',
        'IMG_6829.jpg',
        'IMG_6831.jpg',
        'IMG_6833.jpg',
        'IMG_6838.jpg',
        'IMG_6839.jpg',
        'IMG_7455.jpg',
        'IMG_9141.jpg',
        'IMG_9426.jpg',
        'IMG_9789.jpg',
        '_A1A5569.jpg',      
    ]
        
    
    # find images
    extensions_valides = ('.jpg', '.webp', '.png', '.avif')
    dossier = os.getenv('IMAGES_DIR')

    no = 0
    images = []

    for raw_file in sorted(os.listdir(dossier+'/raw')):
        if raw_file.lower().endswith(extensions_valides):
            try:
                # Raw file
                raw_path = os.path.join(dossier, 'raw', raw_file)
                img = Image.open(raw_path)
                width, height = img.size
                size = os.path.getsize(raw_path)
                image_raw = { 
                    'url' : 'raw/' + raw_file,
                    'name' : raw_file,
                    'width': width,
                    'height': height,
                    'size': round(size/1000)  # ko
                }
                url = image_raw['url']

                # '1024' file
                image_1024 = None
                name_without_extension, extension = os.path.splitext(raw_file)
                avif_file = name_without_extension + ".avif"
                avif_path = os.path.join(dossier, '1024', avif_file)
                
                if os.path.isfile(avif_path):
                    img = Image.open(avif_path)
                    width, height = img.size
                    size = os.path.getsize(avif_path)
                    image_1024 = { 
                        'url' : '1024/' + avif_file,
                        'name' : avif_file,
                        'width': width,
                        'height': height,
                        'size': round(size/1000)  # ko
                    }
                    url = image_1024['url']

                # '480' file
                image_480 = None
                name_without_extension, extension = os.path.splitext(raw_file)
                avif_file = name_without_extension + ".avif"
                avif_path = os.path.join(dossier, '480', avif_file)

                if os.path.isfile(avif_path):
                    img = Image.open(avif_path)
                    width, height = img.size
                    size = os.path.getsize(avif_path)
                    image_480 = { 
                        'url' : '480/' + avif_file,
                        'name' : avif_file,
                        'width': width,
                        'height': height,
                        'size': round(size/1000)  # ko
                    }
                    url = image_480['url']
                    
                # '370' file
                image_370 = None
                name_without_extension, extension = os.path.splitext(raw_file)
                avif_file = name_without_extension + ".avif"
                avif_path = os.path.join(dossier, '370', avif_file)

                if os.path.isfile(avif_path):
                    img = Image.open(avif_path)
                    width, height = img.size
                    size = os.path.getsize(avif_path)
                    image_370 = { 
                        'url' : '370/' + avif_file,
                        'name' : avif_file,
                        'width': width,
                        'height': height,
                        'size': round(size/1000)  # ko
                    }
                    url = image_370['url']

                articles = []

                # search pages using this image
                rows = Article.objects.filter(
                    Q(articlelg__art_text__icontains=avif_file) |
                    Q(art_cover=avif_file)
                ).prefetch_related('articlelg_set').distinct()

                # Sélectionner les champs souhaités
                rows = rows.values(
                    'id',
                    'art_cover',
                    'articlelg__art_slug',
                    'articlelg__language_code',
                )
                for row in rows:
                    articles.append({
                        'id': row['id'],
                        'lg': row['articlelg__language_code'],
                        'slug': row['articlelg__art_slug'],
                        'url': f'/{row['articlelg__language_code']}/{row['articlelg__art_slug']}',
                    })

                no += 1
                images.append(
                  {
                    'no': no,
                    'url': url,
                    'raw': image_raw,
                    '370': image_370,
                    '480': image_480,
                    '1024': image_1024,
                    'articles': articles,
                    'shutterstock': image_raw['name'] in shutterstock_sources,
                    'email': image_raw['name'] in email_sources,
                  }
                )

            except (IOError, OSError):
                continue  # Ignore les fichiers corrompus ou non-images        
    
    return render(
        request,
        'gallery.html',
        {
            "environment": os.getenv('ENVIRONMENT'),            
            "lg": 'en',
            "html": {
                'title': 'Gallery',
                'description': 'Gallery',
            },
            "active": 'gallery',
            "images": images,
            "navbar": Navbar('en').to_json(),
            "hero": {
                "nav": "gallery",
                "image": {
                    "src": "contact.avif",
                    "alt": ""
                },
                "title": "DEV Gallery",
                "subtitle": "DEV Gallery"
            }                    
        }
    )
