from django.shortcuts import render
from django.db import connection
from django.http import HttpResponse, Http404

from jpdev_viz.models import Article, ArticleLg
import markdown2
import re

from .contact_class import *
from .pattern_class import *
from .navbar_class import Navbar


# -----------------------------------------------------------
# Page Article
# Markdow source: https://github.com/trentm/python-markdown2
# ------------------------------------------------------------
def article(request, lg, slug=''):
    #return HttpResponse(f"[DEBUG] le language est : {lg}")

    # Read article data from database
    hero, article = get_article_by_slug(lg, slug)

    all_languages = ['fr', 'en', 'es']
    other_languages = [lang for lang in all_languages if lang != lg]

#     if article == {}:  # slug not found
#         return render(
#             request,
#             "404.html",
#             {
#                "navbar": Navbar(lg).to_json(),
#                "hero": {
#                     "title": "Jennifer Perseverante.com",
#                     "subtitle": (
#                         "Professional makeup artist in Paris and Ile-de-France"
#                         if lg == "en"
#                         else "Maquilleuse professionnelle à Paris et Ile-de-France"
#                     ),
#                 },
#                 "article": {
#                     "language_code": lg,
#                     "translated_slugs": {"fr": "", "en": "", "es": ""},
#                 },
#                 "contact": Contact(
#                     lg=lg, contact_type="generic"
#                 ).get_texts(),

#             },
#         )

    if article["family"][:7] == "AT_HOME":
        contact_type = "at_home"
    elif article["family"][:7] == "WEDDING":
        contact_type = "wedding"
    elif article["family"][:6] == "STUDIO":
        contact_type = "studio"
    else:
        contact_type = "generic"

    no_section = len(article["sections"])

    map = None
    if article["family"][:6] == "STUDIO":
        map = "STUDIO"
    elif article["family"][:7] == "AT_HOME":
        map = "AT_HOME"

    return render(
        request,
        'article.html',
        {
            "html": {
                "title": article['title'],
                "description": article['description'],
            },            
            'lg': lg,
            'other_languages': other_languages,
            'navbar': Navbar(lg).to_json(),      
            'slug': slug,
            'hero': hero,
            'article': article,
            'map': map,
            "contact_form": Contact(
                lg=lg,
                contact_type=contact_type,
                no_section=no_section,
            ).get_texts(),

            'related_articles':  getRelatedArticles(article, lg)
        },
    )


# -------------------
# Get Artcle by Slug
# -------------------
def get_article_by_slug(lg, slug=None):
    """
    Récupère un article et ses champs localisés à partir du slug et du code langue.
    Compatible avec les modèles Article / ArticleLg définis dans la base.
    """

    sql = """
        SELECT 
            a.id, a.art_date, a.art_cover, a.art_family, a.is_page, 
            al.active, al.art_slug, al.nav, al.art_title, al.art_description, al.art_text AS markdown_text, al.hero_title, al.hero_subtitle
        FROM article AS a
        LEFT JOIN article_lg AS al 
            ON a.id = al.id
            AND al.language_code = %s
        WHERE al.art_slug = %s
        LIMIT 1
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [lg, slug])  # ✅ Protection contre injection SQL
        row = cursor.fetchone()

    if not row:
        raise Http404(f"Aucun article trouvé pour le slug '{slug}' ({lg})")

    # Colonnes correspondant à la requête SQL
    columns = [
        "id", "art_date", "art_cover", "art_family", "is_page",
        "active", "art_slug", "nav", "art_title", "art_description", "markdown_text",
        "hero_title", "hero_subtitle"
    ]

    data = dict(zip(columns, row))

    active = data["active"]

    hero = {
        "nav": data["nav"],
        "image": {
            "src": data["art_cover"],
            "alt": data["art_title"],  # TODO specific db field
        },
        "title": data["hero_title"],
        "subtitle": data["hero_subtitle"],
    }

    sections = parse_sections(data['markdown_text'], lg)
    for section in sections:
        if section["type"] == "TEXT":
            section['titles'], section['subtitles'], section["htmls"], section["images"], section["videos"] = parse_texts(section["markdown"], lg)
        elif section["type"] == "MAIN-TEXT":
            section['titles'], section['subtitles'], section["htmls"], section["images"], section["videos"] = parse_texts(section["markdown"], lg)
        # elif section["type"] == "TEXT-CENTERED":
        #     section["htmls"], section["images"], section["videos"] = manyTextsParse(section["markdown"], lg)
        elif section["type"] == "TEXT-IMAGE":
            section['titles'], section['subtitles'], section["htmls"], section["images"], section["videos"] = parse_text_image(section["markdown"], lg)
        elif section["type"] == "IMAGE-TEXT":
            section['titles'], section['subtitles'], section["htmls"], section["images"], section["videos"] = parse_text_image(section["markdown"], lg)
        elif section["type"] == "IMAGE":
            section['titles'], section['subtitles'], section["htmls"], section["images"], section["videos"] = parse_images(section["markdown"], lg)
        else:
            section['titles'] = []
            section['subtitles'] = []
            section["htmls"] = []
            section["images"] = []
            section["videos"] = []

    article = {
        "id": data["id"],
        "lg": lg,
        "slug": data["art_slug"],
        "active": data["active"],
        "title": data["art_title"],
        "description": data["art_description"],
        "markdown_text": data["markdown_text"],
        "date": data["art_date"],
        "family": data["art_family"],
        "is_page": bool(data["is_page"]) if data["is_page"] is not None else False,
        "cover": data["art_cover"],
        "translated_slugs": get_slugs(data["id"]),
        "sections": sections,
    }
    return hero, article


def get_slugs(article_id):
    """Retourne un dictionnaire {language_code: art_slug} pour un article donné."""
    rows = (
        ArticleLg.objects
        .filter(id=article_id)
        .values('language_code', 'art_slug')
    )    
    return {row['language_code']: row['art_slug'] for row in rows}    
       

# ----------------------------------------------
def parse_sections(s, language_code):
    # Text preprocessing
    sections = []

    p = s.find("[SECTION")

    # No section
    if p == -1:
        section = {}
        section["no"] = 0
        section["style"] = "even"
        section["type"] = "TEXT"
        section["markdown"] = s
        return [section]

    no = 0
    while p != -1:
        section = {}
        section["no"] = no
        section["style"] = "even" if no % 2 == 0 else "odd"

        # type (TEXT, ...)?
        p2 = s.find("]", p + 9)
        section["type"] = s[p + 9 : p2]

        next_p = s.find("[SECTION", p + 8)

        if next_p == -1:
            markdown = s[p2 + 2 :].strip()
        else:
            markdown = s[p2 + 2 : next_p].strip()

        section["markdown"] = Pattern(markdown, language_code).preProcess()
        sections.append(section)

        p = next_p
        no = no + 1
    return sections


# Fonction de remplacement
def remplacer_h4(match):
    contenu = match.group(1)
    return f'''
        <div class="text-with-divider">
          <div class="divider"></div>
          <h4 class="font-italic text-opacity-black">{contenu}</h4>
        </div>'''

def extract_title_subtitle(html):
    # Extract <h3>title</h3>
    match = re.search(r"<h3>(.*?)</h3>", html, re.IGNORECASE | re.DOTALL)
    title = match.group(1) if match else None
    html = html.replace(f'<h3>%s</h3>' % title, '')  # remove title from texte
    if title is not None:
        title = title.replace('<strong>', '').replace('</strong>', '')

    # Extract <h4>subtitle</h4>
    pattern = r'<h4>(.*?)</h4>'

    # Remplacement
    new_html = re.sub(pattern, remplacer_h4, html)    
    
    #match = re.search(r"<h4>(.*?)</h4>", html, re.IGNORECASE | re.DOTALL)
    #subtitle = match.group(1) if match else None
    #html = html.replace(f'<h4>%s</h4>' % subtitle, '')  # remove subtitle from texte
    #if subtitle is not None:
    #    subtitle = subtitle.replace('<strong>', '').replace('</strong>', '')
        
    return title, None, new_html
    

# ----------------------------------------------
# Many texts
# ----------------------------------------------
def parse_texts(text, language_code):
    htmls = []
    titles = []
    subtitles = []

    p = text.find("::")

    while p != -1:
        ss = text[0:p].strip()
        ss = Pattern(ss, language_code).preProcess()
        html = markdown2.markdown(ss.strip())
        html = Pattern(html, language_code).postProcess()  # replace keywords and pattern
        title, subtitle, html = extract_title_subtitle(html)

        htmls.append(html)
        titles.append(title)
        subtitles.append(subtitle)

        text = text[p + 2 :]
        p = text.find("::")

    html = markdown2.markdown(text.strip())
    html = Pattern(html, language_code).postProcess()  # finally replace keywords and pattern
    title, subtitle, html = extract_title_subtitle(html)

    htmls.append(html)
    titles.append(title)
    subtitles.append(subtitle)

    return titles, subtitles, htmls, [], []  # Many titles | Many subtitles | Many texts | No image | No video



# ----------------------------------------------
# 1 image and 1 text
# ----------------------------------------------
def parse_text_image(text, lg):
    p = text.find("![")

    # No image, only text
    if p == -1:
        return [markdown2.markdown(text.strip())], [], []

    p2 = text.find("](", p)
    p3 = text.find(")", p2)
    alt = text[p + 2 : p2]
    url = text[p2 + 2 : p3]
    text = text[:p] + text[p3 + 1 :]

    html = markdown2.markdown(text.strip())
    html = Pattern(html, lg).postProcess()
    title, subtitle, html = extract_title_subtitle(html)

    return [title], [subtitle], [html], [{"alt": alt, "url": url}], []  # One title | One subtitle | One text | One image | No video

# ---------------
# Parse images
# ![alt](image.avif)
# ---------------
def parse_images(text, language_code):
    images = []

    p1 = text.find("![")
    while p1 != -1:
        p2 = text.find("](", p1)
        p3 = text.find(")", p2)
        alt = text[p1 + 2 : p2]
        url = text[p2 + 2 : p3]
        images.append({"alt": alt, "url": url})

        text = text[p3 + 1 :]
        p1 = text.find("![")

    return [], [], [], images, []  # No title | No subtitle | No text | Many images | No video

# ----------------------------
# Return Language from Url
# ----------------------------
def getLanguageFromUrl(url):
    if "/en/" in url:
        return "en"
    elif "/es/" in url:
        return "es"
    else:
        return "fr"
    
    

def getRelatedArticles(article, language_code):
    article_id = article["id"]
    families = article["family"]

    # family1, family2, family3 => "family1", "family2", "family3"
    tabs = families.split(",")
    sql_parts = []
    for tab in tabs:
        sql_parts.append(f"art_family LIKE '%%{tab}%%'")
    sql = " OR ".join(sql_parts)

    # Read Data
    rows = Article.objects.raw(
        f"""
        SELECT 
            article.id,
            article.art_date, article.art_cover, 
            art_slug, hero_title, hero_subtitle
        FROM article
        LEFT OUTER JOIN article_lg ON
			article.id = article_lg.id AND language_code='{language_code}'
        WHERE is_page=0 AND ({sql}) AND article.id<>{article_id}
        ORDER BY art_date DESC
        """
    )

    related_articles = []

    # Add all related articles
    for row in rows:
        related_article = {}
        related_article["lg"] = language_code
        related_article["slug"] = row.art_slug
        related_article["date"] = row.art_date
        related_article["cover"] = row.art_cover.replace("1024", "230")
        related_article["hero"] = {}
        related_article["hero"]["title"] = row.hero_title
        related_article["hero"]["subtitle"] = row.hero_subtitle
        related_articles.append(related_article)

    return related_articles
