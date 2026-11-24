# Markdow source: https://github.com/trentm/python-markdown2

from django.shortcuts import render
from django.db import connection
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.db.models import Q
from django_ratelimit.decorators import ratelimit
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.shortcuts import redirect
from django.urls import reverse

from .models import Article, UxSearch, ArticleTracking, Comment

from datetime import datetime
import markdown2
import os
import re
from urllib.parse import urlparse

from .contact_class import Contact
from .article_class import ArticleService
from .pattern_class import *
from .navbar_class import Navbar

signer = TimestampSigner()


# ----------------------
# Page Article
# ----------------------
@ratelimit(key="ip", rate="3/m", method="POST", block=True)
def article(request, lg, slug=""):
    # return HttpResponse(f"[DEBUG] le language est : {lg}")
    url = request.build_absolute_uri()
    base_url = f"{request.scheme}://{request.get_host()}"

    # Read article data from database
    hero = None
    article = {}
    if lg in ["fr", "en", "es"]:
        hero, article = get_article_by_slug(lg, slug)
    else:
        lg = "fr"
    request.lg = lg  # pour contaxt_processors

    # Filter on Family
    filter = request.GET.get("filter")

    related_title_code, related_articles = get_related_articles(article, lg, filter)
    previous_article, next_article = get_adjacent_articles(article, lg, filter)

    # Article tracking.
    token = request.GET.get("token")
    if token:
        try:
            s = signer.unsign(token, max_age=60 * 60 * 24)
            subscriber_id, article_id = s.split("|")
            ArticleTracking.objects.create(
                subscriber_id=subscriber_id,
                article_id=article_id,
                language_code=lg,
                tracking_date=timezone.now(),
            )
        except (BadSignature, SignatureExpired, ValueError):
            pass  # token invalide, expiré ou format incorrect : on ne fait rien

    all_languages = ["fr", "en", "es"]
    other_languages = [lang for lang in all_languages if lang != lg]

    # parsed_url = urlparse(url)
    # base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    # Page 404 si l'article n'existe pas
    if article == {}:  # slug not found
        subtitle = {
            "fr": "Maquilleuse professionnelle<br>à Paris et Ile-de-France",
            "en": "Professional makeup artist<br>in Paris and Ile-de-France",
            "es": "Maquilladora profesional<br>en París y Île-de-France",
        }
        body = {
            "fr": "<h2>Page non trouvée (404)</h2><p>Oups ! La page que vous cherchez n’existe pas.</p>",
            "en": "<h2>Page not found (404)</h2><p>Oops! The page you are looking for does not exist.</p>",
            "es": "<h2>Página no encontrada (404)</h2><p>¡Uy! La página que buscas no existe.</p>",
        }

        return render(
            request,
            "404.html",
            {
                "environment": os.getenv("ENVIRONMENT"),
                "base_url": base_url,
                "html": {
                    "title": "404 error page" + os.getenv("HTML_TITLE_SUFFIX"),
                    "description": "404 error page",
                },
                "lg": lg,
                "other_languages": other_languages,
                "navbar": Navbar(lg).to_json(),
                "active": None,
                "hero": {
                    "nav": "",
                    "image": {"src": "contact.avif", "alt": ""},
                    "title": "Jennifer Perseverante",
                    "subtitle": subtitle[lg],
                },
                "body": body[lg],
            },
        )

    no_section = len(article["sections"])

    # Send email and save in DB ?
    r = None
    if request.method == "POST" and request.POST.get("contact_type"):
        # Envoi d'un message pour contact
        r = Contact(lg, "generic", url, no_section).process(request)

    # Comment alert ?
    if request.GET.get("message") == "comment_added":
        r = {"status": "SUCCESS", "message": "comment_added", "count": None}
    # Subscription alert ?
    elif request.GET.get("message") == "subscription_email_sent":
        r = {"status": "SUCCESS", "message": "subscription_email_sent", "count": None}
    # Subscription confirmed ?
    elif request.GET.get("message") == "subscription_confirmed":
        r = {"status": "SUCCESS", "message": "subscription_confirmed", "count": None}
    # Unsubscription confirmed ?""
    elif request.GET.get("message") == "unsubscription_confirmed":
        r = {"status": "SUCCESS", "message": "unsubscription_confirmed", "count": None}
    # Contact message added ?""
    elif request.GET.get("message") == "contact_added":
        r = {"status": "SUCCESS", "message": "contact_added", "count": None}

    map = None
    if article["family"] is not None:
        if article["family"][:6] == "STUDIO":
            map = "STUDIO"
        elif article["family"][:7] == "AT_HOME":
            map = "AT_HOME"

    # Affichage des commentaires
    root_comments = None
    if os.getenv("DISPLAY_COMMENTS", "0") == "1":
        comments = Comment.objects.filter(
            art_id=article["id"], com_approved=1
        ).order_by("com_date")

        # Arbre : {parent_id: [commentaires enfants]}
        tree_comments = {}
        for com in comments:
            tree_comments.setdefault(com.com_parent_id, []).append(com)

        # Attacher les enfants à chaque commentaire pour le template
        for com in comments:
            com.enfants = tree_comments.get(com.id, [])
            com.date_lg = ArticleService().get_date_lg(com.com_date, lg, "LONG")

        # Racines : sans parent, ou dont le parent n'est pas dans le queryset
        # (filet de sécurité pour ne jamais perdre un commentaire)
        ids = {c.id for c in comments}
        root_comments = [
            c for c in comments if c.com_parent_id is None or c.com_parent_id not in ids
        ]

    return render(
        request,
        "article.html",
        {
            "environment": os.getenv("ENVIRONMENT"),  # DEV, UAT, PROD
            "project": os.getenv("PROJECT"),  # JP, TB
            "base_url": base_url,
            "html": {
                "title": article["title"] + os.getenv("HTML_TITLE_SUFFIX"),
                "description": article["description"],
            },
            "lg": lg,
            "other_languages": other_languages,
            "navbar": Navbar(lg).to_json(),
            # "active": article["active"],
            "slug": slug,
            "hero": hero,
            "slugs_lg": ArticleService().get_slugs(article["id"]),
            "article": article,
            "with_article_date": int(os.getenv("DISPLAY_ARTICLE_DATE")),
            "map": map,
            "contact_form": Contact(lg, "generic", url, no_section).get_texts(),
            "response": r,
            "related_title_code": related_title_code,
            "related_articles": related_articles,
            "previous_article": previous_article,
            "next_article": next_article,
            "filter": filter,
            "families": get_families(lg),
            "root_comments": root_comments,
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
        # raise Http404(f"Aucun article trouvé pour le slug '{slug}' ({lg})")
        return {}, {}

    # Colonnes correspondant à la requête SQL
    columns = [
        "id",
        "art_date",
        "art_cover",
        "art_family",
        "is_page",
        "active",
        "art_slug",
        "nav",
        "art_title",
        "art_description",
        "markdown_text",
        "hero_title",
        "hero_subtitle",
    ]

    data = dict(zip(columns, row))

    is_page = bool(data["is_page"]) if data["is_page"] is not None else False
    blog_link = f'<a href="/{lg}/blog">Blog</a>'

    hero = {
        "nav": blog_link if not is_page else data["nav"],
        "image": {
            "src": data["art_cover"],
            "alt": data["art_title"],  # TODO specific db field
        },
        "title": data["hero_title"],
        "subtitle": data["hero_subtitle"],
    }

    sections = parse_sections(data["markdown_text"], lg)
    for section in sections:
        if section["type"] == "TEXT":
            (
                section["titles"],
                section["subtitles"],
                section["htmls"],
                section["images"],
                section["videos"],
            ) = parse_texts(section["markdown"], lg)
        elif section["type"] == "MAIN-TEXT":
            (
                section["titles"],
                section["subtitles"],
                section["htmls"],
                section["images"],
                section["videos"],
            ) = parse_texts(section["markdown"], lg)
        # elif section["type"] == "TEXT-CENTERED":
        #     section["htmls"], section["images"], section["videos"] = manyTextsParse(section["markdown"], lg)
        elif section["type"] == "TEXT-IMAGE":
            (
                section["titles"],
                section["subtitles"],
                section["htmls"],
                section["images"],
                section["videos"],
            ) = parse_text_image(section["markdown"], lg)
        elif section["type"] == "IMAGE-TEXT":
            (
                section["titles"],
                section["subtitles"],
                section["htmls"],
                section["images"],
                section["videos"],
            ) = parse_text_image(section["markdown"], lg)
        elif section["type"] == "IMAGE":
            (
                section["titles"],
                section["subtitles"],
                section["htmls"],
                section["images"],
                section["videos"],
            ) = parse_images(section["markdown"], lg)
        else:
            section["titles"] = []
            section["subtitles"] = []
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
        "families": get_families(lg),
        "date": data["art_date"],
        "date_lg": ArticleService().get_date_lg(data["art_date"], lg, "LONG"),
        "family": data["art_family"],
        "is_page": is_page,
        "cover": data["art_cover"],
        "translated_slugs": ArticleService().get_slugs(data["id"]),
        "sections": sections,
    }

    return hero, article


# ----------------------------------------------
def parse_sections(s, language_code):
    # Text preprocessing
    sections = []

    p = s.find("[SECTION")

    # No section
    if p == -1:
        return []

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
    return f"""
        <div class="text-with-divider">
          <div class="divider"></div>
          <h4 class="text-opacity-black">{contenu}</h4>
        </div>"""


def extract_title_subtitle(html):
    # Extract <h3>title</h3>
    match = re.search(r"<h3>(.*?)</h3>", html, re.IGNORECASE | re.DOTALL)
    title = match.group(1) if match else None
    html = html.replace(f"<h3>%s</h3>" % title, "")  # remove title from text
    if title is not None:
        title = title.replace("<strong>", "").replace("</strong>", "")

    # Extract <h4>subtitle</h4>
    pattern = r"<h4>(.*?)</h4>"

    # Remplacement
    new_html = re.sub(pattern, remplacer_h4, html)

    # match = re.search(r"<h4>(.*?)</h4>", html, re.IGNORECASE | re.DOTALL)
    # subtitle = match.group(1) if match else None
    # html = html.replace(f'<h4>%s</h4>' % subtitle, '')  # remove subtitle from texte
    # if subtitle is not None:
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
        html = Pattern(
            html, language_code
        ).postProcess()  # replace keywords and pattern
        title, subtitle, html = extract_title_subtitle(html)

        htmls.append(html)
        titles.append(title)
        subtitles.append(subtitle)

        text = text[p + 2 :]
        p = text.find("::")

    html = markdown2.markdown(text.strip())
    html = Pattern(
        html, language_code
    ).postProcess()  # finally replace keywords and pattern
    title, subtitle, html = extract_title_subtitle(html)

    htmls.append(html)
    titles.append(title)
    subtitles.append(subtitle)

    return (
        titles,
        subtitles,
        htmls,
        [],
        [],
    )  # Many titles | Many subtitles | Many texts | No image | No video


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

    return (
        [title],
        [subtitle],
        [html],
        [{"alt": alt, "url": url}],
        [],
    )  # One title | One subtitle | One text | One image | No video


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

    return (
        [],
        [],
        [],
        images,
        [],
    )  # No title | No subtitle | No text | Many images | No video


def get_adjacent_articles(article, lg, filter=None):

    if not article or article.get("is_page"):
        return None, None

    article_id = article["id"]
    article_date = article["date"]

    # Filtre de catégorie éventuel
    family_sql = ""
    params_base = [lg]

    if filter:
        family_sql = " AND a.art_family = %s"
        params_base.append(filter.upper())

    def get_one(direction):
        condition = ""

        # All articles are displayed in DEV environment
        if os.getenv("ENVIRONMENT") != "DEV":
            condition += " AND is_displayed=1"

        if direction == "previous":
            # Article plus récent
            condition += """
                AND (
                    a.art_date > %s
                    OR (a.art_date = %s AND a.id > %s)
                )
            """
            ordering = "a.art_date ASC, a.id ASC"

        else:
            # Article plus ancien
            condition += """
                AND (
                    a.art_date < %s
                    OR (a.art_date = %s AND a.id < %s)
                )
            """
            ordering = "a.art_date DESC, a.id DESC"

        sql = f"""
            SELECT
                a.id,
                a.art_date,
                a.art_cover,
                a.art_family,
                al.art_slug,
                al.art_title,
                al.hero_title,
                al.hero_subtitle
            FROM article a
            INNER JOIN article_lg al
                ON a.id = al.id
                AND al.language_code = %s
            WHERE
                a.is_page = 0
                AND al.art_slug IS NOT NULL
                {family_sql}
                {condition}
            ORDER BY {ordering}
            LIMIT 1
        """

        params = params_base + [article_date, article_date, article_id]

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            row = cursor.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "date": row[1],
            "cover": row[2],
            "family": row[3],
            "slug": row[4],
            "title": row[5],
            "hero_title": row[6],
            "hero_subtitle": row[7],
        }

    previous_article = get_one("previous")
    next_article = get_one("next")

    return previous_article, next_article


def get_related_articles(article, lg, filter):
    article_id = article["id"]
    families = article["family"]

    sql = ""

    # All articles are displayed in DEV environment
    if os.getenv("ENVIRONMENT") != "DEV":
        sql += " AND is_displayed=1"

    if filter is not None:
        # a filter is defined = > use it
        sql += f" AND art_family = '{filter.upper()}'"
        nb = 24
        related_title_code = "LATEST_ARTICLES"
    else:
        if families is None:
            # The Home page  ou About page => 3 last articles
            nb = 3
            related_title_code = "LATEST_ARTICLES"
        elif families.upper() == "ALL":
            # The Blog generic page => no filter
            nb = 24
            related_title_code = "LATEST_ARTICLES"
        else:
            # family1, family2, family3 => "family1", "family2", "family3"
            tabs = families.split(",")
            if len(tabs) == 1:
                sql += f" AND art_family = '{families.upper()}'"
            else:
                sql_parts = []
                for tab in tabs:
                    sql_parts.append(f"art_family LIKE '%%{tab}%%'")
                sql = " AND ("
                sql += " OR ".join(sql_parts)
                sql += ")"
            nb = 6
            related_title_code = "RELATED_ARTICLES"

    # Read Data
    rows = Article.objects.raw(
        f"""
        SELECT 
            article.id,
            article.art_date, article.art_cover, 
            art_slug, hero_title, hero_subtitle
        FROM article
        LEFT OUTER JOIN article_lg ON
			article.id = article_lg.id AND language_code='{lg}'
        WHERE is_page=0 {sql} AND article.id<>{article_id}
        ORDER BY art_date DESC
        LIMIT {nb}
        """
    )

    related_articles = []

    # Add all related articles
    for row in rows:
        related_article = {
            "lg": lg,
            "slug": row.art_slug,
            "date": row.art_date,
            "date_lg": ArticleService().get_date_lg(row.art_date, lg, "SHORT"),
            "cover": row.art_cover.replace("1024", "230") if row.art_cover else None,
            "hero": {"title": row.hero_title, "subtitle": row.hero_subtitle},
        }

        related_articles.append(related_article)

    return related_title_code, related_articles


def get_families(lg):
    # Read Data
    rows = Article.objects.raw(
        f"""
        SELECT 
            family.id,
            family.fam_code,
            family.fam_name
        FROM family
        WHERE fam_lg='{lg}'
        ORDER BY fam_name ASC
        """
    )
    families = []

    # Add all families
    for row in rows:
        family = {
            "code": row.fam_code,
            "name": row.fam_name,
        }

        families.append(family)

    return families


# ------------------
# Search Article
# ------------------
def search(request, lg):
    """Search pattern in hero_title, hero_subtitle and art_text"""
    url = request.build_absolute_uri()

    all_languages = ["fr", "en", "es"]
    other_languages = [lang for lang in all_languages if lang != lg]

    # Read parameters
    query = request.GET.get("p", "").strip()

    # Store search text in DB
    ux_search = UxSearch(
        datetime=datetime.now(),
        language_code=lg,
        search_url=request.META.get("HTTP_REFERER", "/"),
        search_text=query,
        user_agent=request.headers.get("User-Agent"),
    )
    ux_search.save()

    rows = (
        Article.objects.filter(
            Q(articlelg__hero_title__icontains=query)
            | Q(articlelg__hero_subtitle__icontains=query)
            | Q(articlelg__art_text__icontains=query),
            articlelg__language_code=lg,
        )
        .prefetch_related("articlelg_set")
        .distinct()
        .order_by("-art_date")
    )

    # Sélectionner les champs souhaités
    rows = rows.values(
        "id",
        "art_date",
        "art_family",
        "art_cover",
        "is_page",
        "articlelg__art_slug",
        "articlelg__art_title",
        "articlelg__hero_title",
        "articlelg__hero_subtitle",
    )

    articles = []
    i = 0
    for row in rows:
        article = {}
        article["no"] = i
        article["id"] = row["id"]
        article["slug"] = row["articlelg__art_slug"]
        article["date"] = row["art_date"]
        article["family"] = row["art_family"]
        article["is_page"] = row["is_page"]
        article["hero"] = {"image": {}}
        article["cover"] = row["art_cover"]
        article["alt"] = row["articlelg__art_title"]
        article["title"] = row["articlelg__hero_title"]
        article["subtitle"] = row["articlelg__hero_subtitle"]
        article["style"] = "even" if i % 2 == 0 else "odd"
        articles.append(article)
        i += 1

    # Translations
    if lg == "en":
        html_title_lg = "Search Page"
        html_description_lg = "Search Page"
        nav_lg = "Search"
        title_lg = f"Search on query '{query}'"
    elif lg == "es":
        html_title_lg = "Página de búsqueda"
        html_description_lg = "Página de búsqueda"
        nav_lg = "Buscar"
        title_lg = f"Buscar en la consulta '{query}'"
    else:
        html_title_lg = "Page de recherche"
        html_description_lg = "Page de recherche"
        nav_lg = "Recherche"
        title_lg = f"Recherche sur la requête '{query}'"

    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    return render(
        request,
        "search.html",
        {
            "environment": os.getenv("ENVIRONMENT"),
            "base_url": base_url,
            "html": {
                "title": html_title_lg + os.getenv("HTML_TITLE_SUFFIX"),
                "description": html_description_lg,
            },
            "lg": lg,
            "other_languages": other_languages,
            "navbar": Navbar(lg).to_json(),
            "slug": None,
            "hero": {
                "nav": nav_lg,
                "title": title_lg,
                "subtitle": None,
                "image": {
                    "src": "hero-2.avif",
                    "alt": html_title_lg,
                },
            },
            "articles": articles,
            "rows": rows,
            "row": row,
        },
    )
