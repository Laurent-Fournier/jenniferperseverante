#!/usr/bin/env python3
"""
Description : Send Transbeauté Newsletter

La langue de chaque email est déterminée par le champ
subscriber.language_code.

Usage:
    cd ~/www/tbdev_site/
    cd ~/www/tbuat_site/
    source env/bin/activate
    python scripts/cron_send_newsletter.py
"""

import os
import sys
import time
import smtplib
import mysql.connector

from email.message import EmailMessage
from dotenv import load_dotenv

import django
from django.core.signing import TimestampSigner


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()  # load variables from .env

BASE_DIR = os.getenv("BASE_DIR")
SITE_URL = os.getenv("SITE_URL")

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp-beautifuldata.alwaysdata.net")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_DELAY = float(os.getenv("SMTP_DELAY", "1"))
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_SUBJECT_PREFIX = os.getenv("EMAIL_SUBJECT_PREFIX", "")

# Pour les tests, tu peux fixer un article :
# ARTICLE_ID = 11748

# Pour utiliser automatiquement le dernier article :
ARTICLE_ID = None

# Langue utilisée si le subscriber.language_code est NULL
# ou vide.
DEFAULT_LANGUAGE_CODE = "fr"


# ---------------------------------------------------------------------------
# Django
# ---------------------------------------------------------------------------
def setup_django():
    """Initialise Django."""

    if BASE_DIR not in sys.path:
        sys.path.append(BASE_DIR)

    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "tb_site.settings",
    )

    django.setup()


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
def get_db_connection():
    """Crée une connexion MySQL."""

    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


def get_article(cursor, article_id=None):
    """
    Récupère l'article à envoyer.

    Si article_id est None, récupère le dernier article
    possédant une cover.
    """

    if article_id is None:
        sql = """
            SELECT
                id,
                art_cover
            FROM article
            WHERE id = (
                SELECT MAX(id)
                FROM article
                WHERE art_cover IS NOT NULL
            )
        """
        cursor.execute(sql)

    else:
        sql = """
            SELECT
                id,
                art_cover
            FROM article
            WHERE id = %s
        """

        cursor.execute(sql, (article_id,))

    row = cursor.fetchone()

    if row is None:
        raise ValueError(
            "Aucun article trouvé" + (f" pour id={article_id}" if article_id else "")
        )

    if not row["art_cover"]:
        raise ValueError(f"L'article {row['id']} ne possède pas de cover.")

    return row


def get_article_languages(cursor, article_id):
    """
    Récupère toutes les traductions disponibles pour l'article.

    Retourne un dictionnaire :
        {
            "fr": {...},
            "en": {...},
            "es": {...}
        }
    """

    sql = """
        SELECT
            language_code,
            art_slug,
            art_title,
            art_description
        FROM beautifuldata_transbeaute.article_lg
        WHERE id = %s
    """
    cursor.execute(sql, (article_id,))

    rows = cursor.fetchall()

    if not rows:
        raise ValueError(f"Aucune traduction trouvée pour l'article {article_id}")

    languages = {}

    for row in rows:
        languages[row["language_code"]] = row

    return languages


def get_subscribers(cursor):
    """
    Récupère les abonnés actifs avec leur langue.
    """

    sql = """
        SELECT
            id,
            sub_email,
            sub_pseudo,
            language_code
        FROM subscriber
        WHERE is_active = 1
          AND sub_email IS NOT NULL
          AND sub_email != ''
    """
    cursor.execute(sql)
    return cursor.fetchall()


# ---------------------------------------------------------------------------
# Article
# ---------------------------------------------------------------------------


def build_article(article_row, language_row):
    """
    Construit le dictionnaire article pour une langue donnée.
    """

    article_id = article_row["id"]
    cover = article_row["art_cover"]
    language_code = language_row["language_code"]

    # Remplace uniquement l'extension.
    cover_jpg = cover.rsplit(".", 1)[0] + ".jpg"

    return {
        "id": article_id,
        "language_code": language_code,
        "slug": language_row["art_slug"],
        "title": language_row["art_title"],
        "description": language_row["art_description"],
        "site_url": SITE_URL + "/",
        "cover_url": (f"{SITE_URL}/images/newsletter/{cover_jpg}"),
        "url": None,
        "unsubscribe_url": None,
        "tracking_pixel_url": None,
    }


def build_article_url(article):
    """Construit l'URL de l'article dans la bonne langue."""

    if not article["slug"]:
        return ""

    return f"{SITE_URL}/{article['language_code']}/{article['slug']}"


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------


def read_template(filename):
    """Lit un fichier template UTF-8."""

    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        filename,
    )

    if not os.path.exists(path):
        raise FileNotFoundError(f"Template introuvable : {path}")

    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def load_templates(language_code):
    """
    Charge les templates correspondant à la langue.

    Exemple :
        fr -> newsletter_template_fr.htm
        en -> newsletter_template_en.htm
        es -> newsletter_template_es.htm
    """

    html_filename = f"newsletter_template_{language_code}.htm"

    text_filename = f"newsletter_template_{language_code}.txt"

    return (
        read_template(html_filename),
        read_template(text_filename),
    )


# ---------------------------------------------------------------------------
# Personalisation
# ---------------------------------------------------------------------------


def create_subscriber_article(
    article,
    subscriber_id,
    signer,
):
    """
    Crée les URLs personnalisées pour un abonné.

    L'article original n'est pas modifié.
    """

    personalized_article = article.copy()

    language_code = article["language_code"]

    # URL de désinscription
    unsubscribe_token = signer.sign(str(subscriber_id))

    personalized_article["unsubscribe_url"] = (
        f"{SITE_URL}/{language_code}/unsubscribe/{unsubscribe_token}"
    )

    # Token de tracking
    tracking_token = signer.sign(f"{subscriber_id}|{article['id']}")

    personalized_article["tracking_pixel_url"] = (
        f"{SITE_URL}/tracking-pixel/{tracking_token}/"
    )

    # URL de l'article
    personalized_article["url"] = build_article_url(article)

    return personalized_article


def fill_template(
    template,
    subscriber_id,
    article,
):
    """Remplace les variables du template."""

    replacements = {
        "{{subscriber_id}}": str(subscriber_id),
        "{{cover_url}}": article["cover_url"],
        "{{tracking_pixel_url}}": article["tracking_pixel_url"],
        "{{site_url}}": article["site_url"],
        "{{article_title}}": article["title"],
        "{{article_url}}": article["url"] or "",
        "{{article_description}}": article["description"] or "",
        "{{unsubscribe_url}}": article["unsubscribe_url"],
    }

    for placeholder, value in replacements.items():
        template = template.replace(
            placeholder,
            str(value),
        )

    return template


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------


def create_email(
    subscriber,
    article,
    html_template,
    text_template,
):
    """Construit le message email."""

    subscriber_id = subscriber["id"]

    html_content = fill_template(
        html_template,
        subscriber_id,
        article,
    )

    text_content = fill_template(
        text_template,
        subscriber_id,
        article,
    )

    subject = article["title"]

    if EMAIL_SUBJECT_PREFIX:
        subject = f"{EMAIL_SUBJECT_PREFIX} {subject}"

    message = EmailMessage()

    message["Subject"] = subject
    message["From"] = EMAIL_FROM
    message["To"] = subscriber["sub_email"]

    message.set_content(text_content)

    message.add_alternative(
        html_content,
        subtype="html",
    )

    return message


# ---------------------------------------------------------------------------
# Newsletter
# ---------------------------------------------------------------------------


def send_newsletter(
    subscribers,
    article_row,
    article_languages,
    signer,
):
    """
    Envoie la newsletter en utilisant la langue
    de chaque abonné.
    """

    total = len(subscribers)
    sent = 0
    errors = 0

    print()
    print(f"✅ Nombre d'abonnés : {total}")
    print()

    if not subscribers:
        print("⚠️ Aucun abonné actif.")
        return

    templates_cache = {}

    try:
        with smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT,
            timeout=30,
        ) as server:
            # STARTTLS
            server.starttls()

            # if SMTP_USER and SMTP_PASSWORD:
            #     server.login(
            #         SMTP_USER,
            #         SMTP_PASSWORD,
            #     )

            for index, subscriber in enumerate(
                subscribers,
                start=1,
            ):
                email = subscriber["sub_email"]

                # -------------------------------------------------------
                # Langue de l'abonné
                # -------------------------------------------------------

                language_code = subscriber["language_code"] or DEFAULT_LANGUAGE_CODE

                language_code = language_code.lower().strip()

                print(f"#{index}/{total} {email} langue={language_code}")

                try:
                    # ---------------------------------------------------
                    # Vérification de la traduction
                    # ---------------------------------------------------

                    if language_code not in article_languages:
                        raise ValueError(
                            "Aucune traduction disponible "
                            f"pour l'article "
                            f"{article_row['id']} "
                            f"en langue '{language_code}'"
                        )

                    language_row = article_languages[language_code]

                    # ---------------------------------------------------
                    # Article dans la langue de l'abonné
                    # ---------------------------------------------------

                    article = build_article(
                        article_row,
                        language_row,
                    )

                    # ---------------------------------------------------
                    # Templates dans la langue
                    # ---------------------------------------------------

                    if language_code not in templates_cache:
                        templates_cache[language_code] = load_templates(language_code)

                    (
                        html_template,
                        text_template,
                    ) = templates_cache[language_code]

                    # ---------------------------------------------------
                    # URLs personnalisées
                    # ---------------------------------------------------

                    personalized_article = create_subscriber_article(
                        article,
                        subscriber["id"],
                        signer,
                    )

                    # ---------------------------------------------------
                    # Email
                    # ---------------------------------------------------

                    message = create_email(
                        subscriber,
                        personalized_article,
                        html_template,
                        text_template,
                    )

                    # ---------------------------------------------------
                    # Envoi
                    # ---------------------------------------------------

                    server.send_message(message)

                    sent += 1

                    print(f"    ✅ Email envoyé ({language_code})")

                except smtplib.SMTPException as exc:
                    errors += 1

                    print(f"    ❌ Erreur SMTP : {exc}")

                except Exception as exc:
                    errors += 1

                    print(f"    ❌ Erreur : {exc}")

                if SMTP_DELAY > 0:
                    time.sleep(SMTP_DELAY)

    except smtplib.SMTPException as exc:
        raise RuntimeError(
            "Impossible de se connecter au serveur SMTP "
            f"{SMTP_SERVER}:{SMTP_PORT}: {exc}"
        ) from exc

    print()
    print("========================================")
    print("📊 Résultat")
    print(f"   Total     : {total}")
    print(f"   Envoyés   : {sent}")
    print(f"   Erreurs   : {errors}")
    print("========================================")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():

    # Charge .env avant django.setup()
    load_dotenv()

    setup_django()

    signer = TimestampSigner()

    connection = None
    cursor = None

    try:
        # ---------------------------------------------------------------
        # 1. Connexion DB
        # ---------------------------------------------------------------

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        print("✅ Connexion MySQL OK")

        # ---------------------------------------------------------------
        # 2. Récupération de l'article
        # ---------------------------------------------------------------

        article_row = get_article(
            cursor,
            ARTICLE_ID,
        )

        article_id = article_row["id"]
        cover = article_row["art_cover"]

        print(f"✅ Article ID: {article_id} avec cover: {cover}")

        # ---------------------------------------------------------------
        # 3. Récupération de toutes les traductions
        # ---------------------------------------------------------------

        article_languages = get_article_languages(
            cursor,
            article_id,
        )

        print("✅ Langues disponibles : " + ", ".join(sorted(article_languages.keys())))

        # ---------------------------------------------------------------
        # 4. Récupération des abonnés
        # ---------------------------------------------------------------

        subscribers = get_subscribers(cursor)

        print(f"✅ Abonnés actifs : {len(subscribers)}")

        # ---------------------------------------------------------------
        # 5. Création de la newsletter en DB
        # ---------------------------------------------------------------

        sql = """
            INSERT INTO
                beautifuldata_transbeaute.newsletter
            (
                article_id,
                created_at
            )
            VALUES (%s, NOW())
        """

        cursor.execute(
            sql,
            (article_id,),
        )

        newsletter_id = cursor.lastrowid

        print(f"✅ Newsletter créée en DB (ID: {newsletter_id})")

        # ---------------------------------------------------------------
        # 6. Envoi
        # ---------------------------------------------------------------

        send_newsletter(
            subscribers,
            article_row,
            article_languages,
            signer,
        )

        # ---------------------------------------------------------------
        # 7. Commit
        # ---------------------------------------------------------------

        connection.commit()

        print()
        print("✅ Newsletter terminée.")

    except Exception as exc:
        if connection:
            connection.rollback()

        print()
        print(f"❌ ERREUR FATALE : {exc}")

        raise

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()

        print("🔌 Connexion MySQL fermée.")


if __name__ == "__main__":
    main()
