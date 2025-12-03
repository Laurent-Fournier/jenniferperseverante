from django.shortcuts import render
from django.http import HttpResponse

import os
import os.path
from PIL import Image

from jp_viz.models import Article, ArticleLg

#import markdown2

#from .contact_class import *
#from .pattern_class import *
from .navbar_class import Navbar

# ------------
# Error 404
# ------------
def custom_404(request, exception):
    """
    Vue personnalisée pour les erreurs 404
    """
    return render(request, '404.html', status=404)

def test_404(request):
    response = render(request, '404.html')
    response.status_code = 404
    return response


# ------------
# Robots.txt
# ------------
def robots_txt(request):
    host = request.get_host()

    if os.getenv('ENVIRONMENT') == 'PROD':
        robots_content = f'''
          User-agent: * 
          Allow: /
          Sitemap: https://{host}/sitemap.xml
          '''
    else:
        robots_content = '''
          User-agent: * 
          Disallow: /
          '''
    return HttpResponse(robots_content, content_type="text/plain")


# ------------
# About Us
# ------------
def about_us(request):
    return render(
        request,
        'about_us.html',
        {
            "environment": os.getenv('ENVIRONMENT'),
            'lg':'en',
            "html": {
                "title": 'Jennifer Perseverante - Qui suis-je ?',
                "description": 'Maquillage à domicile par Jennifer Perseverante à Paris et Île-de-France (75, 77, 92, 94, 91). Mon studio maquillage est situé en Seine-et-Marne',
            },            
            'active': 'about-us',
            'navbar': Navbar('en').to_json()
        }
    )

# ------------
# Page demo
# ------------
def demo(request):
    return render(
        request,
        'demo.html',
        {
            "environment": os.getenv('ENVIRONMENT'),
            "lg": 'en',
            "html": {
                'title': 'Page demo',
                'description': 'Page demo',
            },
            "active": 'demo',
            "navbar": Navbar('en').to_json()            
        }
    )

# ------------
# Sitemap
# ------------
def sitemap(request):
    scheme = request.scheme  # https://
    host = request.get_host()  # jp-dev.beautifuldata.fr
    host = f"{scheme}://{host}"
    xml_data = ''

    # request on articles
    rows = Article.objects.raw("""
        SELECT 
            article.id, article.art_date, article.is_page,
            article_lg.art_slug, article_lg.language_code
        FROM article
        LEFT OUTER JOIN article_lg ON
            article.id = article_lg.id
        ORDER BY 
            is_page DESC, 
            art_date DESC,
            id DESC,
            CASE language_code
                WHEN 'fr' THEN 1
                WHEN 'en' THEN 2
                WHEN 'es' THEN 3
                ELSE 4
			END
        """)

    xml_data += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'

    for row in rows:
        if row.id == 1:
            priority = 1
        elif row.is_page == 1:
            priority = 0.8
        else:
            priority = 0.5

        if row.language_code == 'fr':
            xml_data +=     '<url>\n'
            xml_data +=         f'<loc>{host}/fr/{row.art_slug}</loc>\n'
            xml_data +=         f'<lastmod>{row.art_date}</lastmod>\n'
            xml_data +=         f'<changefreq>weekly</changefreq>\n'
            xml_data +=         f'<priority>{priority}</priority>\n'
            xml_data +=         f'<xhtml:link rel="alternate" hreflang="fr" href="{host}/fr/{row.art_slug}" />\n'
        elif row.language_code == 'en':
            xml_data +=         f'<xhtml:link rel="alternate" hreflang="en" href="{host}/en/{row.art_slug}" />\n'
        elif row.language_code == 'es':
            xml_data +=         f'<xhtml:link rel="alternate" hreflang="es" href="{host}/es/{row.art_slug}" />\n'
            xml_data +=     '</url>\n'
        else:
            print('ERREUR !!!!!')

    xml_data += '</urlset>\n'

    # Retourner la réponse HTTP avec le type MIME correct
    response = HttpResponse(xml_data, content_type="application/xml")
    response['Content-Disposition'] = 'inline; filename="sitemap.xml"'
    return response
