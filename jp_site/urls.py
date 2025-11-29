from django.http import HttpResponsePermanentRedirect
from django.contrib import admin
from django.urls import path, re_path
from django.views.generic.base import RedirectView

from jp_viz import views, views_article, views_contact, views_media, views_gallery

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

    # DEV Pages
    path('demo', views.demo),
    path('gallery', views_gallery.gallery),

    # Search Page
    path('<str:lg>/search', views_article.search),

    # Article page
    path('<str:lg>/<slug:slug>', views_article.article),

    # Images
    path('images/<int:width>/<str:image_name>', views_media.image),
    
    path('about-us', views.about_us),

    # test erreur 404
    path('test-404', views.test_404),
    
    # redirections 301
    path('maquillage-rouge-levres', RedirectView.as_view(url='/fr/maquillage-rouge-levres', permanent=True)),
    path('maquillage-smoky-eye', RedirectView.as_view(url='/fr/maquillage-smoky-eye', permanent=True)),
    path('home', RedirectView.as_view(url='/fr/', permanent=True)),
    path('maquillage-contouring', RedirectView.as_view(url='/fr/maquillage-contouring', permanent=True)),
    path('maquillage-sourcil', RedirectView.as_view(url='/fr/maquillage-sourcils', permanent=True)),
    path('maquillage-fond-teint', RedirectView.as_view(url='/fr/maquillage-fond-teint', permanent=True)),
    path('maquillage-mariee', RedirectView.as_view(url='/fr/cinq-etapes-maquillage-mariee', permanent=True)),
    path('maquillage-shooting-photo', RedirectView.as_view(url='/fr/maquillage-shooting-photo', permanent=True)),
    path('maquillage-mariage', RedirectView.as_view(url='/fr/maquillage-mariage', permanent=True)),
    path('maquillage-fete', RedirectView.as_view(url='/fr/maquillage-fete', permanent=True)),
    path('jennifer-perseverante-maquillage-domicile', RedirectView.as_view(url='/fr/jennifer-perseverante-maquilleuse-professionnelle', permanent=True)),
    path('temoignages-maquillage-domicile', RedirectView.as_view(url='/fr/temoignages-maquillage', permanent=True)),
    path('halloween-maquillage-deguisement', RedirectView.as_view(url='/fr/halloween-maquillage-deguisement', permanent=True)),
    path('dutiliser-vaseline-cosmetique', RedirectView.as_view(url='/fr/maquillage-vaseline-cosmetique', permanent=True)),
    path('lhuile-ricin-pousser', RedirectView.as_view(url='/fr/huile-ricin-cils', permanent=True)),
    path('maquillage-choisir-grasses', RedirectView.as_view(url='/fr/maquillage-peaux-grasses', permanent=True)),
    path('comment-reussir-maquillage', RedirectView.as_view(url='/fr/comment-reussir-maquillage', permanent=True)),
    path('vous-recherchez-la-photographe-ideal-pour-votre-mariage', RedirectView.as_view(url='/fr/vous-recherchez-la-photographe-ideal-pour-votre-mariage', permanent=True)),
    path('vous-recherchez-lorganisatrice-de-mariage-ideal', RedirectView.as_view(url='/fr/vous-recherchez-organisatrice-de-mariage-ideal', permanent=True)),
    path('ne-sous-estimez-pas-votre-budget-maquillage-pour-le-jour-j', RedirectView.as_view(url='/fr/ne-sous-estimez-pas-votre-budget-maquillage-pour-le-jour-j', permanent=True)),
    path('makeup-workshop', RedirectView.as_view(url='/fr/cours-de-maquillage', permanent=True)),
    path('et-pourquoi-pas-un-atelier-maquillage-pour-lanniversaire-de-votre-enfant', RedirectView.as_view(url='/fr/atelier-maquillage-anniversaire-enfant', permanent=True)),
    path('pinceaux-maquillage-utiliser', RedirectView.as_view(url='/fr/pinceaux-maquillage-professionnels', permanent=True)),
    path('tutoriel-maquillage-euro-2016', RedirectView.as_view(url='/fr/tutoriel-maquillage-bleu-blanc-rouge', permanent=True)),
    path('atelier-maquillage-evjf', RedirectView.as_view(url='/fr/atelier-maquillage-enterrement-vie-jeune-fille', permanent=True)),
    path('decouvrir-nouveau-maquillage', RedirectView.as_view(url='/fr/decouvrir-nouvel-studio-maquillage', permanent=True)),
    path('offrez-cadeau-maquillage', RedirectView.as_view(url='/fr/offrez-cadeau-maquillage', permanent=True)),
    path('chouchou-semaine-guerlain', RedirectView.as_view(url='/fr/chouchou-semaine-guerlain', permanent=True)),
    path('comment-regimes-maigrir', RedirectView.as_view(url='/fr/comment-regimes-maigrir', permanent=True)),
    path('produit-chouchou-mascara', RedirectView.as_view(url='/fr/produit-chouchou-mascara', permanent=True)),
    path('feminiser-visage-conseils-trangenres', RedirectView.as_view(url='/fr/feminiser-visage-conseils-transgenres', permanent=True)),
    path('maquillage-professionnels-beaute', RedirectView.as_view(url='/fr/maquillage-professionnels-beaute', permanent=True)),
    path('cours-maquillage-professionnels', RedirectView.as_view(url='/fr/cours-maquillage-professionnels', permanent=True)),
    path('studio-maquillage', RedirectView.as_view(url='/fr/studio-maquillage-en-seine-et-marne', permanent=True)),
    path('chouchou-semaine-nars', RedirectView.as_view(url='/fr/chouchou-semaine-creme-teintee-nars', permanent=True)),
    path('chouchou-latelier-maquillage', RedirectView.as_view(url='/fr/produit-chouchou-crayon-sourcil-atelier-maquillage', permanent=True)),
    path('grossesse-feminine-enceinte', RedirectView.as_view(url='/fr/grossesse-feminine-enceinte', permanent=True)),
    path('presidentielles-apparence-conseils', RedirectView.as_view(url='/fr/presidentielles-apparence-conseils', permanent=True)),
    path('cadeau-moment-complicite', RedirectView.as_view(url='/fr/cadeau-moment-complicite', permanent=True)),
    path('entreprise', RedirectView.as_view(url='/fr/entreprise', permanent=True)),
    path('chouchou-semaine-benefit', RedirectView.as_view(url='/fr/produit-chouchou-semaine-blush-benefit', permanent=True)),
    path('maquillage-hommes-demploi', RedirectView.as_view(url='/fr/maquillage-hommes', permanent=True)),
    path('maquilleuse-professionnelle-formation', RedirectView.as_view(url='/fr/formation-maquilleuse-professionnelle', permanent=True)),
    path('optez-mariage-hippie', RedirectView.as_view(url='/fr/optez-mariage-hippie-chic', permanent=True)),
    path('vivier-feeriques-mariages', RedirectView.as_view(url='/fr/vivier-lieux-feeriques-pour-mariages', permanent=True)),
    path('concours-maquillage-personnes', RedirectView.as_view(url='/fr/concours-maquillage-pour-trois-personnes', permanent=True)),
    path('adolescentes-accompagner-feminite', RedirectView.as_view(url='/fr/cours-maquillage-pour-adolescentes', permanent=True)),
    path('camoufler-tatouage-maquillage', RedirectView.as_view(url='/fr/camoufler-tatouage-maquillage', permanent=True)),
    path('transgenres-personnes-transition', RedirectView.as_view(url='/fr/transgenres-personnes-transition', permanent=True)),
    path('enterrement-jeune-fille', RedirectView.as_view(url='/fr/maquillage-enterrement-vie-jeune-fille', permanent=True)),
    path('maquillage-anticipation-mariage', RedirectView.as_view(url='/fr/maquillage-anticipation-mariage', permanent=True)),
    path('maquillage-mariage-anticiper', RedirectView.as_view(url='/fr/maquillage-mariage-anticiper', permanent=True)),
    path('idees-cadeaux-maquillage', RedirectView.as_view(url='/fr/idees-cadeaux-maquillage', permanent=True)),
    path('confiance-maquillage-professionnel', RedirectView.as_view(url='/fr/confiance-maquillage-professionnel', permanent=True)),
    path('qualites-maquilleuse-mariage', RedirectView.as_view(url='/fr/qualites-maquilleuse-mariage', permanent=True)),
    path('les-merveilles-cachees-des-ateliers-de-maquillage', RedirectView.as_view(url='/fr/les-merveilles-cachees-des-ateliers-de-maquillage', permanent=True)),
    path('ma-maquilleuse-me-pose-un-lapin-pour-mon-mariage-que-faire', RedirectView.as_view(url='/fr/ma-maquilleuse-me-pose-un-lapin-pour-mon-mariage', permanent=True)),
    path('optimiser-maquillage-conseils', RedirectView.as_view(url='/fr/optimiser-maquillage-mariage', permanent=True)),
    path('studio-maquillage-chevry', RedirectView.as_view(url='/fr/studio-maquillage-chevry', permanent=True)),
    path('maquillage-mariage-hack', RedirectView.as_view(url='/fr/maquillage-mariage-hack', permanent=True)),
    path('choisir-maquillage-mariage', RedirectView.as_view(url='/fr/choisir-maquillage-mariage', permanent=True)),
    path('ateliers-maquillage-cadeau', RedirectView.as_view(url='/fr/ateliers-maquillage-cadeau', permanent=True)),
    path('maquillage-cossigny-perseverante', RedirectView.as_view(url='/fr/atelier-maquillage-chevry-cossigny', permanent=True)),

]

