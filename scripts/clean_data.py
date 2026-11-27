#!/usr/bin/env python
"""
Description : Clean Data

cd ~/www/tbdev_site/
source env/bin/activate
python scripts/clean_data.py
"""

import mysql.connector

import os
from dotenv import load_dotenv

IMAGE_DIR = "/home/beautifuldata/www/tbdev_site/staticfiles/images/raw"


def find_wrong_images(directory, wrong_chaine, recursive=True):
    """List of image filenames containing a given character string"""
    wrong_chaine = wrong_chaine.lower()
    results = []
    if recursive:
        for racine, _, fichiers in os.walk(directory):
            for f in fichiers:
                if wrong_chaine in f.lower():
                    results.append(os.path.join(racine, f))
    else:
        for f in os.listdir(directory):
            chemin = os.path.join(directory, f)
            if os.path.isfile(chemin) and wrong_chaine in f.lower():
                results.append(chemin)
    return sorted(results)


def find_wrong_articles_string(cursor, column, wrong_chaine):
    """List of articles in the database containing a given character string"""
    sql = f"""
        SELECT 
            article.id, article_lg.language_code, article_lg.art_slug, 
            article_lg.art_title, article_lg.art_description  
        FROM article
        LEFT OUTER JOIN article_lg
          ON article.id = article_lg.id
        WHERE article_lg.{column} LIKE "%{wrong_chaine}%"
        ORDER BY article.art_date DESC
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    return rows


def find_wrong_articles_length(cursor, column, min_length, max_length):
    """List of items in the database with an incorrect length"""
    sql = f"""
        SELECT 
            article.id, article_lg.language_code, article_lg.art_slug, 
            article_lg.art_title, article_lg.art_description,
            CHAR_LENGTH(article_lg.{column}) AS length
        FROM article
        LEFT OUTER JOIN article_lg
          ON article.id = article_lg.id
        WHERE 
            (
                CHAR_LENGTH(article_lg.{column}) < {min_length}
                OR
                CHAR_LENGTH(article_lg.{column}) > {max_length}
            )
        ORDER BY article.art_date DESC
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    return rows


def main():
    load_dotenv()  # load variables from .env

    with_details = True

    connexion = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )
    cursor = connexion.cursor(dictionary=True)

    # 1. Liste des images contenant le terme 'Perseverante'
    images = find_wrong_images(IMAGE_DIR, "Perseverante", True)
    print(f'[test 1] {len(images)} images contenant "Perseverante" dans leur nom')

    if with_details:
        i = 0
        for i, f in enumerate(images):
            print("")
            print(f"{i + 1}. {os.path.basename(f)}")

            new_image = os.path.splitext(os.path.basename(f))[0] + ".avif"
            # print(new_image)
            articles = find_wrong_articles_string(cursor, "art_text", new_image)
            for j, article in enumerate(articles):
                print(
                    f"\t{j + 1}. #{article['id']} {article['language_code']} {article['art_slug']}"
                )

    # 2. Liste des articles contenant le terme 'Perseverante' dans leur titre
    articles = find_wrong_articles_string(cursor, "art_title", "Perseverante")
    print(f'[test 2] {len(articles)} articles contenant "Perseverante" dans leur titre')

    if with_details:
        for i, article in enumerate(articles):
            print(
                f"\t{j + 1}. #{article['id']} {article['language_code']} {article['art_slug']}"
            )
            print(f"\t{article['art_slug']}")

    # 3. Liste des articles contenant le terme 'Perseverante' dans leur description
    articles = find_wrong_articles_string(cursor, "art_description", "Perseverante")
    print(
        f'[test 3] {len(articles)} articles contenant "Perseverante" dans leur description'
    )

    if with_details:
        for i, article in enumerate(articles):
            print(f"{i + 1}. #{article['id']} {article['art_description']}")
            print(f"\t{article['art_slug']}")

    # 4. Liste des articles contenant le terme 'Perseverante' dans leur contenu
    articles = find_wrong_articles_string(cursor, "art_text", " Perseverante")
    print(f'[test 4] {len(articles)} articles contenant "Perseverante" dans leur text')

    if with_details:
        for i, article in enumerate(articles):
            print(
                f"\t{i + 1}. #{article['id']} {article['language_code']} {article['art_slug']}"
            )

    # 5. Liste des articles ayant une longueur de titre incorrecte
    articles = find_wrong_articles_length(cursor, "art_title", 30, 60)
    print(f"[test 5] {len(articles)} articles ayant une longueur de titre incorrecte")

    if with_details:
        for i, article in enumerate(articles):
            print(
                f"\t{i + 1}. #{article['id']} {article['language_code']} {article['art_title']} {article['length']} characters [30..60]"
            )

    # 6. Liste des articles ayant une longueur de descriptif incorrecte
    articles = find_wrong_articles_length(cursor, "art_description", 150, 160)
    print(
        f"[test 6] {len(articles)} articles ayant une longueur de description incorrecte"
    )

    if with_details:
        for i, article in enumerate(articles):
            print(
                f"\t{i + 1}. #{article['id']} {article['language_code']} {article['art_description']} {article['length']} characters [150..160]"
            )


if __name__ == "__main__":
    main()
