from django.http import HttpResponsePermanentRedirect
from django.contrib import admin
from django.urls import path, re_path

from jpdev_viz import views, views_article, views_media

def redirect_to_fr(request):
    return HttpResponsePermanentRedirect('/fr/')

urlpatterns = [
    path('robots.txt', views.robots_txt, name='robots_txt'), 
    path('admin/', admin.site.urls),
    
    # Sitemap
    path('sitemap.xml', views.sitemap, name='sitemap'),    

    # Root '/' redirect to '/fr/'
    re_path(r'^$', redirect_to_fr, name='redirect-to-fr'),

    # Home page
    path('<str:lg>/', views.article),
    
    # Article page
    path('<str:lg>/<slug:slug>', views_article.article),

    # Images
    path('images/<int:width>/<str:image_name>', views_media.image),
    
    path('', views.index),
    path('about-us', views.about_us),
    path('demo', views.demo),

]
