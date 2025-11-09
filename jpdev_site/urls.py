from django.http import HttpResponsePermanentRedirect
from django.contrib import admin
from django.urls import path, re_path
from django.conf.urls import handler404

from jpdev_viz import views, views_article, views_contact, views_media

handler404 = 'salsalive_viz.views.custom_404'

def redirect_to_fr(request):
    return HttpResponsePermanentRedirect('/fr/')

urlpatterns = [
    path('robots.txt', views.robots_txt, name='robots_txt'), 
    path('sitemap.xml', views.sitemap, name='sitemap'),    
    path('admin/', admin.site.urls),
    
    # Root '/' redirect to '/fr/'
    re_path(r'^$', redirect_to_fr, name='redirect-to-fr'),

    # Home page
    path('<str:lg>/', views_article.article),

    # Contact Page
    path('fr/contact', views_contact.generic),
    path('en/contact-us', views_contact.generic),
    path('es/contacto', views_contact.generic),

    # Demo Page
    path('fr/demo', views.demo),
    path('en/demo', views.demo),
    path('es/demo', views.demo),

    # Search Page
    path('<str:lg>/search', views.search),

    # Article page
    path('<str:lg>/<slug:slug>', views_article.article),

    # Images
    path('images/<int:width>/<str:image_name>', views_media.image),
    
    path('about-us', views.about_us),

    # test erreur 404
    path('test-404', views.test_404),     
]
