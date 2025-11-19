from django.shortcuts import render
from django.http import HttpResponse

from django.db.models import Q

from .models import Article, ArticleLg

import os
import os.path
from PIL import Image

from .navbar_class import Navbar
    
# ------------
# Gallery
# ------------
def gallery(request):
    
    # find images
    extensions_valides = ('.jpg', '.webp', '.png', '.avif')
    dossier = '/home/beautifuldata/www/jpdev_site/staticfiles/images/'

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
                  }
                )

            except (IOError, OSError):
                continue  # Ignore les fichiers corrompus ou non-images        
    
    return render(
        request,
        'gallery.html',
        {
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
