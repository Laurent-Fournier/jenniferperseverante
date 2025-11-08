from django.shortcuts import render
from django.http import HttpResponse

from jpdev_viz.models import Article, ArticleLg

#import markdown2

from .contact_class import *
from .pattern_class import *
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
# Home page
# ------------
def index(request):
    return render(
        request,
        'index.html',
        {
            'title': 'JenniferPerseverante - Jennifer Perseverante, maquilleuse professionnelle pour mariage, atelier de maquillage, maquillage à domicile',
            'description': 'Jennifer Perseverante, maquilleuse professionnelle pour mariage, atelier de maquillage, maquillage à domicile',
            'active': 'home',
            'lg':'fr'
        }
    )
    
# ------------
# Robots.txt
# ------------
def robots_txt(request):
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
# demo
# ------------
def demo(request):
    return render(
        request,
        'demo.html',
        {
            "lg": 'en',
            "html": {
                'title': 'Demo',
                'description': 'Demo',
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



# -------------------
# Get Artcle by Slug
# -------------------
def getArticleBySlug(lg, slug):
    article={}
    article['id']=1
    article["title"] = 'TMP Laurent'
    article["description"] = 'TMP Laurent'
    article['family']='HOME_PAGE'
    article["sections"] = []
    return {}, article  # TODO remove
    
    
    rows = ArticleLg.objects.raw(
        f"""
        SELECT 
            article_lg.id,
            article.art_date, article.art_cover, article.art_family, article.is_page,
            art_slug, art_title, art_description, art_text AS markdown_text, 
            hero_title, hero_subtitle
        FROM article
        LEFT OUTER JOIN article_lg ON
			article.id = article_lg.id AND language_code='{language_code}'
        WHERE art_slug='{slug}'
        """
    )

    article = {}
    hero = {}

    # parse all sections in markdown text
    for row in rows:
        sections = sectionsParse(row.markdown_text, language_code)

        article["slug"] = slug
        article["language_code"] = language_code

        article["id"] = row.id
        article["title"] = row.art_title
        article["description"] = row.art_description
        article["date"] = row.art_date
        article["family"] = row.art_family
        article["is_page"] = row.is_page

        hero["image"] = {}
        hero["image"]["src"] = row.art_cover
        hero["image"]["alt"] = row.art_title  # TODO specific db field ?
        hero["title"] = row.hero_title
        hero["subtitle"] = row.hero_subtitle

        article["sections"] = sections

        for section in sections:
            if section["type"] == "TEXT":
                # section['htmls'] = [markdown2.markdown(section['markdown'].strip())]
                # section['images'] = []
                section["htmls"], section["images"], section["videos"] = manyTextsParse(
                    section["markdown"], language_code
                )
            elif section["type"] == "TEXT-CENTERED":
                section["htmls"], section["images"], section["videos"] = manyTextsParse(
                    section["markdown"], language_code
                )
            elif section["type"] == "TEXT-IMAGE":
                section["htmls"], section["images"], section["videos"] = oneImageParse(
                    section["markdown"], language_code
                )
            elif section["type"] == "IMAGE-TEXT":
                section["htmls"], section["images"], section["videos"] = oneImageParse(
                    section["markdown"], language_code
                )
            elif section["type"] == "IMAGE":
                section["htmls"], section["images"], section["videos"] = parseImages(
                    section["markdown"], language_code
                )
            else:
                section["htmls"] = []
                section["images"] = []
                section["videos"] = []

        article["translated_slugs"] = getSlugs(article["id"])
    return hero, article


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


# -----------------------------------------------------------
# Page Article
# Markdow source: https://github.com/trentm/python-markdown2
# ------------------------------------------------------------
def article(request, lg, slug=""):
    url = request.build_absolute_uri()
    language_code = getLanguageFromUrl(url)
    r = None

    # Send email and save in DB ?
    #if request.method == "POST":
    #    r = Contact(language_code, "generic", url).process(request)

    # Read article data from database
    hero, article = getArticleBySlug(lg, slug)

    if article == {}:  # slug not found
        return render(
            request,
            "404.html",
            {
               "navbar": Navbar(lg).to_json(),
               "hero": {
                    "title": "Jennifer Perseverante.com",
                    "subtitle": (
                        "Professional makeup artist in Paris and Ile-de-France"
                        if lg == "en"
                        else "Maquilleuse professionnelle à Paris et Ile-de-France"
                    ),
                },
                "article": {
                    "language_code": lg,
                    "translated_slugs": {"fr": "", "en": "", "es": ""},
                },
                "contact": Contact(
                    language_code=lg, contact_type="generic"
                ).get_texts(),

            },
        )

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
        style = "even" if no_section % 2 == 0 else "odd"
        map = {"type": "STUDIO", "style": style}
        no_section += 1
    elif article["family"][:7] == "AT_HOME":
        style = "even" if no_section % 2 == 0 else "odd"
        map = {"type": "AT_HOME", "style": style}
        no_section += 1

    return render(
        request,
        "index.html", # TODO: Update
        {
            "lg": lg,
            "html": {
                "title": article["title"],
                "description": article["description"],
            },
            "navbar": Navbar(lg).to_json(),
            "hero": hero,
            "article": article,
            "map": map,
            "contact_form": Contact(
                language_code=lg,
                contact_type=contact_type,
                no_section=no_section,
            ).get_texts(),
            "related_articles": getRelatedArticles(
                article, lg, no_section + 1
            ),  # With a related articles section ?
            "response": r,
        },
    )
    
    
# ----------------------------------------------
def sectionsParse(s, language_code):
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



def getRelatedArticles(article, language_code, no_section):
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
    i = 0
    for row in rows:
        related_article = {}

        related_article["col"] = i % 4  # 4 columns
        related_article["language_code"] = language_code
        related_article["style"] = "even" if no_section % 2 == 0 else "odd"
        related_article["slug"] = row.art_slug
        related_article["date"] = row.art_date
        related_article["cover"] = row.art_cover.replace("1024", "230")

        related_article["hero"] = {}
        related_article["hero"]["title"] = row.hero_title
        related_article["hero"]["subtitle"] = row.hero_subtitle

        related_articles.append(related_article)
        i += 1

    return related_articles



# ------------------
# Search Page
# ------------------
def search(request, lg):

    all_languages = ['fr', 'en', 'es']
    other_languages = [lang for lang in all_languages if lang != lg]

    # Read parameters
    pattern = request.GET.get("p").strip()

    if len(pattern)<2:
        rows = []
    else:  # TODO à protéger contre les injections SQL
        rows = Article.objects.raw(
            f"""
            SELECT 
                article.id,
                article.art_date, article.art_cover, article.art_family, article.is_page,
                art_slug, art_title, art_text, 
                hero_title, hero_subtitle
            FROM article
            LEFT OUTER JOIN article_lg ON
			    article.id = article_lg.id AND language_code='{lg}'
            WHERE 
                article_lg.hero_title LIKE '%%{pattern}%%' OR
                article_lg.hero_subtitle LIKE '%%{pattern}%%' OR
                article_lg.art_text LIKE '%%{pattern}%%'
            ORDER BY is_page DESC, art_date DESC
            """
        )
    articles = []

    i = 0
    for row in rows:
        article = {}
        article["no"] = i
        article["id"] = row.id
        article["slug"] = row.art_slug
        article["date"] = row.art_date
        article["family"] = row.art_family
        article["is_page"] = row.is_page
        article["hero"] = {"image": {}}
        article["cover"] = row.art_cover
        article["alt"] = row.art_title
        article["title"] = row.hero_title
        article["subtitle"] = row.hero_subtitle
        article["style"] = 'even' if i%2 == 0 else 'odd'
        articles.append(article)
        i += 1

    return render(request, "search.html",
        {
            "html": None,
            'lg': lg,
            'other_languages': other_languages,
            'navbar': Navbar(lg).to_json(),      
            'slug': 'aaaa',
            "hero": {
                "title": f"Search on word '{pattern}'",
                "subtitle": pattern,
                "image": {
                    "src": "hero-2.avif",
                    "alt": "Image de la page de recherche",
                },
            },
            "articles": articles,
        },
    )
